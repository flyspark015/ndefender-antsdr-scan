import unittest

from ndefender_antsdr_scan.classification import classify_signal, SignalFeatures


class ClassificationTests(unittest.TestCase):
    def test_wideband_low_burst(self) -> None:
        features = SignalFeatures(
            freq_hz=5_800_000_000,
            band="5G8",
            snr_db=20.0,
            bandwidth_class="wide",
            burstiness=0.1,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path[:2], ["Analog", "Video"])
        self.assertGreaterEqual(result.confidence, 0.6)

    def test_narrowband_bursty(self) -> None:
        features = SignalFeatures(
            freq_hz=2_400_000_000,
            band="2G4",
            snr_db=12.0,
            bandwidth_class="narrow",
            burstiness=0.9,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path[0], "Control")
        self.assertGreaterEqual(result.confidence, 0.7)

    def test_unknown(self) -> None:
        features = SignalFeatures(
            freq_hz=900_000_000,
            band="900",
            snr_db=5.0,
            bandwidth_class="",
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path, ["Unknown"])


if __name__ == "__main__":
    unittest.main()
