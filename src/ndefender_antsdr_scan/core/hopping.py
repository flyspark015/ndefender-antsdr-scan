from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class HopRateEstimator:
    window_ms: int = 1000
    min_hop_hz: float = 200000.0

    def __post_init__(self) -> None:
        if self.window_ms <= 0:
            raise ValueError("window_ms must be positive")
        if self.min_hop_hz < 0:
            raise ValueError("min_hop_hz must be non-negative")
        self._samples: deque[tuple[int, float]] = deque()

    def update(self, freq_hz: float, timestamp_ms: int) -> float:
        self._samples.append((timestamp_ms, freq_hz))
        self._trim(timestamp_ms)
        return self._compute_rate()

    def _trim(self, now_ms: int) -> None:
        cutoff = now_ms - self.window_ms
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _compute_rate(self) -> float:
        if len(self._samples) < 2:
            return 0.0
        hops = 0
        prev_freq = self._samples[0][1]
        for _, freq in list(self._samples)[1:]:
            if abs(freq - prev_freq) >= self.min_hop_hz:
                hops += 1
                prev_freq = freq
        duration_ms = max(self._samples[-1][0] - self._samples[0][0], 1)
        duration_s = duration_ms / 1000.0
        return hops / duration_s
