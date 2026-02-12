from __future__ import annotations

from .models import ClassificationResult, SignalFeatures
from .profiles import ProfileSet
from .rules import RuleContext, classify


class Classifier:
    def __init__(self, profiles: ProfileSet | None = None, ctx: RuleContext | None = None) -> None:
        self._profiles = profiles
        self._ctx = ctx

    def classify(self, features: SignalFeatures) -> ClassificationResult:
        if self._profiles is not None:
            result = self._profiles.classify(features)
            if result is not None:
                return result
        return classify(features, self._ctx)


def classify_signal(features: SignalFeatures, ctx: RuleContext | None = None) -> ClassificationResult:
    return classify(features, ctx)
