from __future__ import annotations

from dataclasses import dataclass

from ndefender_antsdr_scan.core import dsp
from ndefender_antsdr_scan.tracking.models import FeatureHints
from .base import Detection, SpectrumFrame


@dataclass(frozen=True)
class PeakDetectorConfig:
    min_snr_db: float
    lo_guard_hz: float


class PeakDetector:
    def __init__(self, config: PeakDetectorConfig) -> None:
        self._config = config

    def detect(self, frame: SpectrumFrame) -> list[Detection]:
        if len(frame.freqs_hz) != len(frame.power_db):
            raise ValueError("freqs_hz and power_db must be same length")
        if not frame.freqs_hz:
            return []

        noise_floor = dsp.noise_floor_db(frame.power_db)
        threshold = noise_floor + self._config.min_snr_db
        detections: list[Detection] = []

        for idx in dsp.local_maxima_indices(frame.power_db):
            peak_db = frame.power_db[idx]
            snr_db = peak_db - noise_floor
            if snr_db < self._config.min_snr_db:
                continue

            freq_hz = frame.freqs_hz[idx]
            if frame.lo_hz is not None:
                if abs(freq_hz - frame.lo_hz) <= self._config.lo_guard_hz:
                    continue

            prominence_db = max(0.0, peak_db - max(frame.power_db[idx - 1], frame.power_db[idx + 1]))
            cluster_size = dsp.contiguous_cluster_size(frame.power_db, idx, threshold_db=threshold)
            bandwidth_class = "wide" if cluster_size >= 10 else "narrow"

            detections.append(
                Detection(
                    freq_hz=freq_hz,
                    band=frame.band,
                    snr_db=snr_db,
                    peak_db=peak_db,
                    noise_floor_db=noise_floor,
                    bandwidth_class=bandwidth_class,
                    features=FeatureHints(
                        prominence_db=prominence_db,
                        cluster_size=cluster_size,
                        pattern_hint="unknown",
                        hop_hint="none",
                    ),
                )
            )

        return detections
