from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from ndefender_antsdr_scan.detectors.base import Detection, Detector, SpectrumFrame
from ndefender_antsdr_scan.io.emit import EventEmitter
from ndefender_antsdr_scan.classification import classify_signal, SignalFeatures
from ndefender_antsdr_scan.tracking.models import FeatureHints
from ndefender_antsdr_scan.tracking.tracker import Tracker, make_observation


class Clock(Protocol):
    def __call__(self) -> int:
        ...


@dataclass(frozen=True)
class EngineStats:
    frames_processed: int = 0
    detections_processed: int = 0
    events_emitted: int = 0


class ScanEngine:
    def __init__(self, detector: Detector, tracker: Tracker, emitter: EventEmitter, clock: Clock | None = None) -> None:
        self._detector = detector
        self._tracker = tracker
        self._emitter = emitter
        self._clock = clock
        self._stats = EngineStats()

    @property
    def stats(self) -> EngineStats:
        return self._stats

    def process_frame(self, frame: SpectrumFrame) -> list[dict]:
        detections = self._detector.detect(frame)
        observations = _detections_to_observations(detections, frame.timestamp_ms)
        events = self._tracker.ingest(observations)
        self._emitter.emit_many(events)

        self._stats = EngineStats(
            frames_processed=self._stats.frames_processed + 1,
            detections_processed=self._stats.detections_processed + len(detections),
            events_emitted=self._stats.events_emitted + len(events),
        )
        return events

    def flush(self) -> list[dict]:
        if self._clock is None:
            return []
        now_ms = int(self._clock())
        events = self._tracker.ingest([], now_ms=now_ms)
        self._emitter.emit_many(events)
        if events:
            self._stats = EngineStats(
                frames_processed=self._stats.frames_processed,
                detections_processed=self._stats.detections_processed,
                events_emitted=self._stats.events_emitted + len(events),
            )
        return events


def _detections_to_observations(detections: Iterable[Detection], timestamp_ms: int):
    return [
        make_observation(
            freq_hz=det.freq_hz,
            band=det.band,
            snr_db=det.snr_db,
            peak_db=det.peak_db,
            noise_floor_db=det.noise_floor_db,
            bandwidth_class=det.bandwidth_class,
            features=_augment_features(det),
            timestamp_ms=timestamp_ms,
        )
        for det in detections
    ]


def _augment_features(detection: Detection) -> FeatureHints:
    base = detection.features
    classification = classify_signal(
        SignalFeatures(
            freq_hz=detection.freq_hz,
            band=detection.band,
            snr_db=detection.snr_db,
            bandwidth_class=detection.bandwidth_class,
            prominence_db=base.prominence_db,
            cluster_size=base.cluster_size,
            pattern_hint=base.pattern_hint,
            hop_hint=base.hop_hint,
        )
    )
    return FeatureHints(
        prominence_db=float(base.prominence_db),
        cluster_size=int(base.cluster_size),
        pattern_hint=str(base.pattern_hint),
        hop_hint=str(base.hop_hint),
        class_path=classification.class_path,
        classification_confidence=classification.confidence,
    )
