from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalFeatures:
    freq_hz: float
    band: str
    snr_db: float
    bandwidth_class: str
    bandwidth_est_hz: float | None = None
    burstiness: float | None = None
    hop_rate_hz: float | None = None
    ofdm_score: float | None = None
    modulation_hint: str | None = None
    prominence_db: float | None = None
    cluster_size: int | None = None
    pattern_hint: str | None = None
    hop_hint: str | None = None


@dataclass(frozen=True)
class ClassificationResult:
    class_path: list[str]
    confidence: float
    reason: str
    pattern_hint: str | None = None
