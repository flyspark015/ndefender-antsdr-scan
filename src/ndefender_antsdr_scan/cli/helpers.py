from __future__ import annotations

import time
from typing import Iterable

from ndefender_antsdr_scan.core.config import AppConfig, load_config
from ndefender_antsdr_scan.api.contract import EVENT_TYPES
from ndefender_antsdr_scan.core.engine import ScanEngine
from ndefender_antsdr_scan.core.radio import AntSdrRadio, NullRadio
from ndefender_antsdr_scan.core.sweep import iter_sweep
from ndefender_antsdr_scan.detectors.base import SpectrumFrame
from ndefender_antsdr_scan.detectors.peak import PeakDetector
from ndefender_antsdr_scan.io.emit import EmitConfig, EventEmitter
from ndefender_antsdr_scan.io.jsonl import read_jsonl
from ndefender_antsdr_scan.tracking.tracker import Tracker


def load_app_config(path: str) -> AppConfig:
    return load_config(path)


def build_engine(config: AppConfig, jsonl_path: str | None = None) -> tuple[ScanEngine, EventEmitter]:
    detector = PeakDetector(config.detector)
    tracker = Tracker(config.tracker)
    emitter = EventEmitter(EmitConfig(jsonl_path=jsonl_path) if jsonl_path else None)
    return ScanEngine(detector, tracker, emitter, clock=_now_ms), emitter


def _now_ms() -> int:
    return int(time.time() * 1000)


def run_replay(log_path: str, engine: ScanEngine, emitter: EventEmitter) -> dict:
    frames = 0
    events_emitted = 0
    for record in read_jsonl(log_path):
        if not isinstance(record, dict):
            continue
        if _is_contact_event(record):
            emitter.emit(record)
            events_emitted += 1
            continue

        frame = _frame_from_record(record)
        if frame is None:
            continue
        engine.process_frame(frame)
        frames += 1

    events_emitted += len(engine.flush())
    stats = engine.stats
    return {
        "frames": frames,
        "detections": stats.detections_processed,
        "events_emitted": events_emitted,
    }


def run_stats(log_path: str) -> dict:
    counts = {"RF_CONTACT_NEW": 0, "RF_CONTACT_UPDATE": 0, "RF_CONTACT_LOST": 0}
    total = 0
    last_timestamp = None
    for record in read_jsonl(log_path):
        total += 1
        event_type = record.get("type")
        if event_type in counts:
            counts[event_type] += 1
        ts = record.get("timestamp")
        if ts is not None:
            last_timestamp = ts
    return {
        "total": total,
        "counts": counts,
        "last_timestamp": last_timestamp,
    }


def _is_contact_event(record: dict) -> bool:
    event_type = record.get("type")
    return event_type in EVENT_TYPES and isinstance(record.get("data"), dict)


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


def iter_live_frames(config: AppConfig) -> Iterable[SpectrumFrame]:
    radio = AntSdrRadio(config.radio)
    radio.connect()
    try:
        for step in iter_sweep(config.sweep.bands):
            freqs, power = radio.capture_spectrum(step.lo_hz)
            yield SpectrumFrame(
                freqs_hz=freqs,
                power_db=power,
                timestamp_ms=_now_ms(),
                band=step.band,
                lo_hz=step.lo_hz,
            )
    finally:
        radio.close()


def null_live_frames(config: AppConfig) -> Iterable[SpectrumFrame]:
    null_radio = NullRadio(lambda _lo: ([2_450_000_000], [120.0]))
    for step in iter_sweep(config.sweep.bands):
        freqs, power = null_radio.capture_spectrum(step.lo_hz)
        yield SpectrumFrame(
            freqs_hz=freqs,
            power_db=power,
            timestamp_ms=_now_ms(),
            band=step.band,
            lo_hz=step.lo_hz,
        )
