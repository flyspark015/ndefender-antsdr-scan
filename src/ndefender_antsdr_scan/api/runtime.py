from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ndefender_antsdr_scan.cli.helpers import (
    build_engine,
    iter_live_frames,
    null_live_frames,
)
from ndefender_antsdr_scan.core.config import AppConfig
from ndefender_antsdr_scan.core.engine import ScanEngine
from ndefender_antsdr_scan.detectors.base import SpectrumFrame
from ndefender_antsdr_scan.io.jsonl import read_jsonl
from ndefender_antsdr_scan.api.bus import EventBus
from ndefender_antsdr_scan.io.emit import EventEmitter


@dataclass
class ReplayResult:
    frames: int
    detections: int
    events_emitted: int


class EngineRunner:
    def __init__(
        self,
        config: AppConfig,
        event_bus: EventBus,
        null_radio: bool = False,
        jsonl_path: str | None = None,
        frame_source: callable | None = None,
    ) -> None:
        self._config = config
        self._event_bus = event_bus
        self._null_radio = null_radio
        self._jsonl_path = jsonl_path
        self._frame_source = frame_source
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._engine: ScanEngine | None = None
        self._emitter: EventEmitter | None = None
        self._last_error: Exception | None = None

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    @property
    def last_error(self) -> Exception | None:
        return self._last_error

    @property
    def stats(self):
        engine = self._engine
        return engine.stats if engine is not None else None

    @property
    def ws_connected(self) -> bool:
        emitter = self._emitter
        return emitter.ws_connected if emitter is not None else False

    def start(self) -> bool:
        with self._lock:
            if self.is_running:
                return False
            self._stop_event.clear()
            engine, emitter = build_engine(self._config, jsonl_path=self._jsonl_path, event_bus=self._event_bus)
            self._engine = engine
            self._emitter = emitter
            self._thread = threading.Thread(target=self._run_loop, name="antsdr-scan", daemon=True)
            self._thread.start()
            return True

    def stop(self) -> bool:
        with self._lock:
            if not self.is_running:
                return False
            self._stop_event.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5.0)
        engine = self._engine
        if engine is not None:
            engine.flush()
        return True

    def _run_loop(self) -> None:
        try:
            frame_iter = self._frames()
            for frame in frame_iter:
                if self._stop_event.is_set():
                    break
                assert self._engine is not None
                self._engine.process_frame(frame)
        except Exception as exc:
            self._last_error = exc
        finally:
            if self._engine is not None:
                self._engine.flush()

    def _frames(self) -> Iterable[SpectrumFrame]:
        if self._frame_source is not None:
            return self._frame_source()
        if self._null_radio:
            return null_live_frames(self._config)
        return iter_live_frames(self._config)

    def replay(self, log_path: str, output_path: str | None = None, max_events: int | None = None) -> ReplayResult:
        if self.is_running:
            raise RuntimeError("cannot replay while live scan is running")
        engine, emitter = build_engine(self._config, jsonl_path=output_path, event_bus=self._event_bus)
        frames = 0
        events_emitted = 0
        for record in read_jsonl(log_path):
            if not isinstance(record, dict):
                continue
            event_type = record.get("type")
            if event_type in {"RF_CONTACT_NEW", "RF_CONTACT_UPDATE", "RF_CONTACT_LOST"}:
                emitter.emit(record)
                events_emitted += 1
                if max_events is not None and events_emitted >= max_events:
                    break
                continue
            frame = _frame_from_record(record)
            if frame is None:
                continue
            engine.process_frame(frame)
            frames += 1
            if max_events is not None and events_emitted >= max_events:
                break
        events_emitted += len(engine.flush())
        stats = engine.stats
        return ReplayResult(frames=frames, detections=stats.detections_processed, events_emitted=events_emitted)


def _frame_from_record(record: dict) -> SpectrumFrame | None:
    data = record.get("data") if isinstance(record.get("data"), dict) else record
    if not isinstance(data, dict):
        return None
    freq_hz = data.get("freq_hz")
    peak_db = data.get("peak_db")
    if freq_hz is None or peak_db is None:
        return None
    timestamp_ms = int(record.get("timestamp") or data.get("timestamp") or 0)
    band = str(data.get("band", ""))
    freq = float(freq_hz)
    peak = float(peak_db)
    freqs = [freq - 1.0, freq, freq + 1.0]
    power = [peak - 6.0, peak, peak - 6.0]
    return SpectrumFrame(
        freqs_hz=freqs,
        power_db=power,
        timestamp_ms=timestamp_ms,
        band=band,
        lo_hz=None,
    )
