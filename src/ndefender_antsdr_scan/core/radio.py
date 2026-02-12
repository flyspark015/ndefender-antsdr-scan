from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RadioConfig:
    uri: str
    sample_rate: int


class Radio(Protocol):
    def capture_spectrum(self, lo_hz: float) -> tuple[Sequence[float], Sequence[float]]:
        ...

    def close(self) -> None:
        ...


class AntSdrRadio:
    def __init__(self, config: RadioConfig) -> None:
        self._config = config
        self._device = None

    def connect(self) -> None:
        try:
            import adi  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on hardware
            raise RuntimeError("pyadi-iio is required for AntSDR access") from exc

        self._device = adi.ad9361(uri=self._config.uri)
        self._device.sample_rate = int(self._config.sample_rate)

    def capture_spectrum(self, lo_hz: float) -> tuple[Sequence[float], Sequence[float]]:
        if self._device is None:
            raise RuntimeError("AntSdrRadio not connected")
        raise NotImplementedError("Spectrum capture not implemented yet")

    def close(self) -> None:
        self._device = None


class NullRadio:
    def __init__(self, provider: callable) -> None:
        self._provider = provider

    def capture_spectrum(self, lo_hz: float) -> tuple[Sequence[float], Sequence[float]]:
        return self._provider(lo_hz)

    def close(self) -> None:
        return None
