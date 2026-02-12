from __future__ import annotations

from dataclasses import dataclass

from .models import ClassificationResult, SignalFeatures
from .scoring import score_control


@dataclass(frozen=True)
class RuleContext:
    min_burstiness_for_control: float = 0.6
    min_confidence: float = 0.5


def classify(features: SignalFeatures, ctx: RuleContext | None = None) -> ClassificationResult:
    context = ctx or RuleContext()

    if features.bandwidth_class == "wide":
        if _is_low_burst(features):
            return ClassificationResult(
                class_path=["Analog", "Video", "WideFM"],
                confidence=0.8,
                reason="wideband + low burstiness",
            )
        return ClassificationResult(
            class_path=["Analog", "Video"],
            confidence=0.6,
            reason="wideband signal",
        )

    if features.bandwidth_class == "narrow":
        if _is_hopping(features):
            boost = _control_confidence_boost(features)
            return ClassificationResult(
                class_path=["Control", "Hopping"],
                confidence=min(0.8 + boost, 0.9),
                reason="narrowband + hopping",
            )
        if _is_bursty(features, context.min_burstiness_for_control):
            boost = _control_confidence_boost(features)
            return ClassificationResult(
                class_path=["Control", "Burst"],
                confidence=min(0.75 + boost, 0.9),
                reason="narrowband + bursty",
            )
        return ClassificationResult(
            class_path=["Control"],
            confidence=0.55,
            reason="narrowband signal",
        )

    return ClassificationResult(class_path=["Unknown"], confidence=0.2, reason="no rule match")


def _is_bursty(features: SignalFeatures, threshold: float) -> bool:
    if features.burstiness is None:
        return False
    return features.burstiness >= threshold


def _is_low_burst(features: SignalFeatures) -> bool:
    if features.burstiness is None:
        return False
    return features.burstiness <= 0.2


def _is_hopping(features: SignalFeatures) -> bool:
    if features.hop_rate_hz is None:
        return False
    return features.hop_rate_hz >= 1.0


def _control_confidence_boost(features: SignalFeatures) -> float:
    return score_control(features) * 0.1
