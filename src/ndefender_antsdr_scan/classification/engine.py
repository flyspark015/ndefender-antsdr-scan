from __future__ import annotations

from .models import ClassificationResult, SignalFeatures
from .rules import RuleContext, classify


def classify_signal(features: SignalFeatures, ctx: RuleContext | None = None) -> ClassificationResult:
    return classify(features, ctx)
