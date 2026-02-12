from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(frozen=True)
class BandPlan:
    name: str
    start_hz: float
    stop_hz: float
    step_hz: float


@dataclass(frozen=True)
class SweepStep:
    band: str
    lo_hz: float


def iter_sweep(bands: Iterable[BandPlan]) -> Iterator[SweepStep]:
    for band in bands:
        if band.step_hz <= 0:
            raise ValueError("step_hz must be positive")
        if band.stop_hz < band.start_hz:
            raise ValueError("stop_hz must be >= start_hz")

        lo = band.start_hz
        while lo <= band.stop_hz:
            yield SweepStep(band=band.name, lo_hz=lo)
            lo += band.step_hz
