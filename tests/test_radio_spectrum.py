import unittest

import numpy as np

from ndefender_antsdr_scan.core.radio import spectrum_from_samples


class RadioSpectrumTests(unittest.TestCase):
    def test_spectrum_peak_at_offset(self) -> None:
        sample_rate = 1_000_000
        lo_hz = 2_400_000_000.0
        tone_offset = 100_000.0
        n = 4096
        t = np.arange(n) / sample_rate
        samples = np.exp(2j * np.pi * tone_offset * t)

        freqs, power = spectrum_from_samples(samples, sample_rate, lo_hz)
        max_idx = int(np.argmax(power))
        peak_freq = freqs[max_idx]

        resolution = sample_rate / n
        self.assertLess(abs(peak_freq - (lo_hz + tone_offset)), resolution * 2)


if __name__ == "__main__":
    unittest.main()
