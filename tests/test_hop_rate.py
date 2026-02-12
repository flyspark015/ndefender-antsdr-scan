import unittest

from ndefender_antsdr_scan.core.hopping import HopRateEstimator


class HopRateTests(unittest.TestCase):
    def test_hop_rate(self) -> None:
        estimator = HopRateEstimator(window_ms=1000, min_hop_hz=100.0)
        self.assertEqual(estimator.update(1000.0, 0), 0.0)
        rate = estimator.update(1200.0, 500)
        self.assertGreater(rate, 0.0)

    def test_no_hops(self) -> None:
        estimator = HopRateEstimator(window_ms=1000, min_hop_hz=100.0)
        estimator.update(1000.0, 0)
        rate = estimator.update(1005.0, 500)
        self.assertEqual(rate, 0.0)


if __name__ == "__main__":
    unittest.main()
