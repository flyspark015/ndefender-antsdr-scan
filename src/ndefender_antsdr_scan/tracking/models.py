from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureHints:
    prominence_db: float
    cluster_size: int
    pattern_hint: str
    hop_hint: str
    bandwidth_est_hz: float | None = None
    burstiness: float | None = None
    hop_rate_hz: float | None = None
    class_path: list[str] | None = None
    classification_confidence: float | None = None
    control_correlation: bool | None = None


@dataclass(frozen=True)
class Observation:
    freq_hz: float
    band: str
    snr_db: float
    peak_db: float
    noise_floor_db: float
    bandwidth_class: str
    features: FeatureHints
    timestamp_ms: int


@dataclass
class ContactState:
    id: str
    bucket_value_hz: int
    band: str
    bandwidth_class: str
    hit_count: int
    confirmed: bool
    first_seen_ms: int
    last_seen_ms: int
    last_update_emitted_ms: int | None
    last_emitted_snr_db: float
    last_snr_db: float
    freq_hz: float
    peak_db: float
    noise_floor_db: float
    confidence: float
    features: FeatureHints
    awaiting_correlation: bool = False
