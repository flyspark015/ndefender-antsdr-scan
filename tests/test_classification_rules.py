import unittest

from ndefender_antsdr_scan.classification import classify_signal, SignalFeatures


class ClassificationRuleTests(unittest.TestCase):
    def test_hopping_control(self) -> None:
        features = SignalFeatures(
            freq_hz=915_000_000,
            band="915",
            snr_db=15.0,
            bandwidth_class="narrow",
            hop_rate_hz=5.0,
            burstiness=0.2,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path, ["Control", "Hopping"])

    def test_bursty_control(self) -> None:
        features = SignalFeatures(
            freq_hz=2_440_000_000,
            band="2G4",
            snr_db=12.0,
            bandwidth_class="narrow",
            hop_rate_hz=0.0,
            burstiness=0.9,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path, ["Control", "Burst"])


if __name__ == "__main__":
    unittest.main()
