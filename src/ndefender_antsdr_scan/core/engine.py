from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from ndefender_antsdr_scan.detectors.base import Detection, Detector, SpectrumFrame
from ndefender_antsdr_scan.io.emit import EventEmitter
from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.scoring import score_control
from ndefender_antsdr_scan.core.hopping import HopRateEstimator
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
    def __init__(
        self,
        detector: Detector,
        tracker: Tracker,
        emitter: EventEmitter,
        clock: Clock | None = None,
        classifier: Classifier | None = None,
        hop_window_ms: int = 1000,
        min_hop_hz: float = 200000.0,
    ) -> None:
        self._detector = detector
        self._tracker = tracker
        self._emitter = emitter
        self._clock = clock
        self._classifier = classifier or Classifier()
        self._hop_window_ms = hop_window_ms
        self._min_hop_hz = min_hop_hz
        self._hop_estimators: dict[str, HopRateEstimator] = {}
        self._stats = EngineStats()

    @property
    def stats(self) -> EngineStats:
        return self._stats

    def process_frame(self, frame: SpectrumFrame) -> list[dict]:
        detections = self._detector.detect(frame)
        observations = self._detections_to_observations(detections, frame.timestamp_ms)
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


    def _detections_to_observations(self, detections: Iterable[Detection], timestamp_ms: int):
        return [
        make_observation(
            freq_hz=det.freq_hz,
            band=det.band,
            snr_db=det.snr_db,
            peak_db=det.peak_db,
            noise_floor_db=det.noise_floor_db,
            bandwidth_class=det.bandwidth_class,
            features=self._augment_features(det, timestamp_ms),
            timestamp_ms=timestamp_ms,
        )
        for det in detections
        ]


    def _augment_features(self, detection: Detection, timestamp_ms: int) -> FeatureHints:
        base = detection.features
        hop_rate_hz = self._hop_rate_for(detection.band, detection.freq_hz, timestamp_ms)
        ofdm_score = None
        if base.bandwidth_est_hz is not None or base.burstiness is not None:
            from ndefender_antsdr_scan.classification.ofdm import ofdm_signature_score

            ofdm_score = ofdm_signature_score(
                SignalFeatures(
                    freq_hz=detection.freq_hz,
                    band=detection.band,
                    snr_db=detection.snr_db,
                    bandwidth_class=detection.bandwidth_class,
                    bandwidth_est_hz=base.bandwidth_est_hz,
                    burstiness=base.burstiness,
                )
            )

        classification = self._classifier.classify(
            SignalFeatures(
                freq_hz=detection.freq_hz,
                band=detection.band,
                snr_db=detection.snr_db,
                bandwidth_class=detection.bandwidth_class,
                bandwidth_est_hz=base.bandwidth_est_hz,
                burstiness=base.burstiness,
                hop_rate_hz=hop_rate_hz,
                ofdm_score=ofdm_score,
                prominence_db=base.prominence_db,
                cluster_size=base.cluster_size,
                pattern_hint=base.pattern_hint,
                hop_hint=base.hop_hint,
            )
        )
        control_score = score_control(
            SignalFeatures(
                freq_hz=detection.freq_hz,
                band=detection.band,
                snr_db=detection.snr_db,
                bandwidth_class=detection.bandwidth_class,
                bandwidth_est_hz=base.bandwidth_est_hz,
                burstiness=base.burstiness,
                hop_rate_hz=hop_rate_hz,
                prominence_db=base.prominence_db,
                cluster_size=base.cluster_size,
                pattern_hint=base.pattern_hint,
                hop_hint=base.hop_hint,
            )
        )
        pattern_hint = classification.pattern_hint or base.pattern_hint
        return FeatureHints(
            prominence_db=float(base.prominence_db),
            cluster_size=int(base.cluster_size),
            pattern_hint=str(pattern_hint),
            hop_hint=str(base.hop_hint),
            bandwidth_est_hz=base.bandwidth_est_hz,
            burstiness=base.burstiness,
            hop_rate_hz=hop_rate_hz,
            control_score=control_score,
            class_path=classification.class_path,
            classification_confidence=classification.confidence,
            control_correlation=base.control_correlation,
        )

    def _hop_rate_for(self, band: str, freq_hz: float, timestamp_ms: int) -> float:
        estimator = self._hop_estimators.get(band)
        if estimator is None:
            estimator = HopRateEstimator(window_ms=self._hop_window_ms, min_hop_hz=self._min_hop_hz)
            self._hop_estimators[band] = estimator
        return estimator.update(freq_hz, timestamp_ms)
