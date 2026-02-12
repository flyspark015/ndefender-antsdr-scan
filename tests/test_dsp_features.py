import unittest

from ndefender_antsdr_scan.core.dsp import estimate_bandwidth_hz, estimate_burstiness


class DspFeatureTests(unittest.TestCase):
    def test_estimate_bandwidth(self) -> None:
        freqs = [0.0, 1.0, 2.0, 3.0]
        power = [-10.0, 5.0, 5.0, -10.0]
        bw = estimate_bandwidth_hz(freqs, power, threshold_db=0.0)
        self.assertEqual(bw, 1.0)

    def test_estimate_burstiness(self) -> None:
        power = [0.0, -1.0, 2.0, -2.0]
        burst = estimate_burstiness(power, threshold_db=0.0)
        self.assertEqual(burst, 0.5)


if __name__ == "__main__":
    unittest.main()
