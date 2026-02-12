from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

from .models import ClassificationResult, SignalFeatures


@dataclass(frozen=True)
class ProfileRule:
    name: str
    start_hz: float
    stop_hz: float
    class_path: list[str]
    pattern_hint: str | None = None
    bandwidth_class: str | None = None
    min_snr_db: float | None = None
    confidence: float = 0.85
    requires_ofdm_score: float | None = None
    priority: int = 0

    def matches(self, features: SignalFeatures) -> bool:
        if not (self.start_hz <= features.freq_hz <= self.stop_hz):
            return False
        if self.bandwidth_class and features.bandwidth_class != self.bandwidth_class:
            return False
        if self.min_snr_db is not None and features.snr_db < self.min_snr_db:
            return False
        if self.requires_ofdm_score is not None:
            if features.ofdm_score is None or features.ofdm_score < self.requires_ofdm_score:
                return False
        return True

    def distance_to(self, freq_hz: float) -> float:
        center = (self.start_hz + self.stop_hz) / 2.0
        return abs(freq_hz - center)


@dataclass(frozen=True)
class ProfileSet:
    rules: list[ProfileRule]

    def classify(self, features: SignalFeatures) -> ClassificationResult | None:
        candidates = [rule for rule in self.rules if rule.matches(features)]
        if not candidates:
            return None
        candidates.sort(
            key=lambda rule: (
                -rule.priority,
                rule.distance_to(features.freq_hz),
                -rule.confidence,
            )
        )
        rule = candidates[0]
        confidence = _profile_confidence(rule, features)
        return ClassificationResult(
            class_path=rule.class_path,
            confidence=confidence,
            reason=f"profile:{rule.name}",
            pattern_hint=rule.pattern_hint,
        )


def load_profiles(path: str | Path) -> ProfileSet:
    raw = _load_yaml(Path(path))
    entries = raw.get("profiles", []) if isinstance(raw, dict) else []
    rules = [
        ProfileRule(
            name=str(entry.get("name", "")),
            start_hz=float(entry.get("start_hz", 0.0)),
            stop_hz=float(entry.get("stop_hz", 0.0)),
            class_path=[str(item) for item in entry.get("class_path", [])],
            pattern_hint=entry.get("pattern_hint"),
            bandwidth_class=entry.get("bandwidth_class"),
            min_snr_db=float(entry["min_snr_db"]) if "min_snr_db" in entry else None,
            confidence=float(entry.get("confidence", 0.85)),
            requires_ofdm_score=float(entry["requires_ofdm_score"]) if "requires_ofdm_score" in entry else None,
            priority=int(entry.get("priority", 0)),
        )
        for entry in entries
    ]
    return ProfileSet(rules=rules)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("classification profiles must be a mapping")
    return data


def _profile_confidence(rule: ProfileRule, features: SignalFeatures) -> float:
    if not rule.class_path or rule.class_path[0] != "Analog":
        return rule.confidence
    confidence = rule.confidence
    min_snr = rule.min_snr_db if rule.min_snr_db is not None else 10.0
    snr_excess = max(0.0, features.snr_db - min_snr)
    confidence += min(snr_excess / 20.0 * 0.1, 0.1)
    if features.prominence_db is not None:
        prominence = max(0.0, features.prominence_db)
        confidence += min(prominence / 30.0 * 0.05, 0.05)
    return min(confidence, 0.95)
