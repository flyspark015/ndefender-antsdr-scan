from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ndefender_antsdr_scan.tracking.models import FeatureHints


@dataclass(frozen=True)
class SpectrumFrame:
    freqs_hz: Sequence[float]
    power_db: Sequence[float]
    timestamp_ms: int
    band: str
    lo_hz: float | None = None


@dataclass(frozen=True)
class Detection:
    freq_hz: float
    band: str
    snr_db: float
    peak_db: float
    noise_floor_db: float
    bandwidth_class: str
    features: FeatureHints


class Detector(Protocol):
    def detect(self, frame: SpectrumFrame) -> list[Detection]:
        ...
