from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class RadioConfig:
    uri: str
    sample_rate: int
    rx_buffer_size: int = 4096


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
        if hasattr(self._device, "rx_rf_bandwidth"):
            self._device.rx_rf_bandwidth = int(self._config.sample_rate)
        if hasattr(self._device, "rx_buffer_size"):
            self._device.rx_buffer_size = int(self._config.rx_buffer_size)
        if hasattr(self._device, "rx_enabled_channels"):
            self._device.rx_enabled_channels = [0]

    def capture_spectrum(self, lo_hz: float) -> tuple[Sequence[float], Sequence[float]]:
        if self._device is None:
            raise RuntimeError("AntSdrRadio not connected")
        self._device.rx_lo = int(lo_hz)
        samples = self._device.rx()
        return spectrum_from_samples(samples, self._config.sample_rate, lo_hz)

    def close(self) -> None:
        self._device = None


class NullRadio:
    def __init__(self, provider: callable) -> None:
        self._provider = provider

    def capture_spectrum(self, lo_hz: float) -> tuple[Sequence[float], Sequence[float]]:
        return self._provider(lo_hz)

    def close(self) -> None:
        return None


def spectrum_from_samples(
    samples: Sequence[complex] | np.ndarray,
    sample_rate: int,
    lo_hz: float,
) -> Tuple[list[float], list[float]]:
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    samples_arr = np.asarray(samples)
    if samples_arr.ndim > 1:
        samples_arr = samples_arr[0]
    samples_arr = samples_arr.astype(np.complex64, copy=False)
    if samples_arr.size == 0:
        raise ValueError("samples cannot be empty")

    window = np.hanning(samples_arr.size)
    spectrum = np.fft.fftshift(np.fft.fft(samples_arr * window))
    power_db = 20.0 * np.log10(np.abs(spectrum) + 1e-12)
    freqs = np.fft.fftshift(np.fft.fftfreq(samples_arr.size, d=1.0 / sample_rate))
    freqs_hz = freqs + lo_hz
    return freqs_hz.tolist(), power_db.tolist()
