from __future__ import annotations

from statistics import median
from typing import Iterable, Sequence


def noise_floor_db(power_db: Sequence[float]) -> float:
    if not power_db:
        raise ValueError("power_db cannot be empty")
    return float(median(power_db))


def local_maxima_indices(power_db: Sequence[float]) -> Iterable[int]:
    if len(power_db) < 3:
        return []
    maxima = []
    for idx in range(1, len(power_db) - 1):
        if power_db[idx] > power_db[idx - 1] and power_db[idx] > power_db[idx + 1]:
            maxima.append(idx)
    return maxima


def contiguous_cluster_size(power_db: Sequence[float], idx: int, threshold_db: float) -> int:
    if not (0 <= idx < len(power_db)):
        return 0
    size = 1
    left = idx - 1
    while left >= 0 and power_db[left] >= threshold_db:
        size += 1
        left -= 1
    right = idx + 1
    while right < len(power_db) and power_db[right] >= threshold_db:
        size += 1
        right += 1
    return size
