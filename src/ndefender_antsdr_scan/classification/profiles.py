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
        return ClassificationResult(
            class_path=rule.class_path,
            confidence=rule.confidence,
            reason=f"profile:{rule.name}",
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
