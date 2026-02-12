import unittest

from ndefender_antsdr_scan.classification import SignalFeatures, classify_signal


class VendorHeuristicTests(unittest.TestCase):
    def test_dji_hint(self) -> None:
        features = SignalFeatures(
            freq_hz=5_780_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            bandwidth_est_hz=20_000_000,
            burstiness=0.5,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path[-1], "DJI")

    def test_walksnail_hint(self) -> None:
        features = SignalFeatures(
            freq_hz=5_900_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            bandwidth_est_hz=20_000_000,
            burstiness=0.5,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path[-1], "Walksnail")

    def test_hdzero_hint(self) -> None:
        features = SignalFeatures(
            freq_hz=5_620_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            bandwidth_est_hz=20_000_000,
            burstiness=0.5,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path[-1], "HDZero")


if __name__ == "__main__":
    unittest.main()
