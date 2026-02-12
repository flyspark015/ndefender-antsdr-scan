from __future__ import annotations

from .models import SignalFeatures


def ofdm_signature_score(features: SignalFeatures) -> float:
    score = 0.0
    if features.bandwidth_est_hz is not None:
        if 12_000_000 <= features.bandwidth_est_hz <= 30_000_000:
            score += 0.4
        elif 8_000_000 <= features.bandwidth_est_hz < 12_000_000:
            score += 0.2
    if features.burstiness is not None and 0.2 <= features.burstiness <= 0.8:
        score += 0.3
    if features.snr_db >= 10.0:
        score += 0.2
    if features.bandwidth_class == "wide":
        score += 0.1
    return min(score, 1.0)
