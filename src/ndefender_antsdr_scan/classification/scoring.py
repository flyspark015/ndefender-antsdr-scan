from __future__ import annotations

from .models import SignalFeatures


def score_control(features: SignalFeatures) -> float:
    score = 0.0
    band = features.band.upper()
    if "2G4" in band or "915" in band or "900" in band:
        score += 0.1
    if features.bandwidth_class == "narrow":
        score += 0.1
    if features.hop_rate_hz is not None and features.hop_rate_hz >= 1.0:
        score += 0.4
    if features.burstiness is not None and features.burstiness >= 0.6:
        score += 0.3
    return min(score, 1.0)
