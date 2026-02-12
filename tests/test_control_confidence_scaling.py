import unittest

from ndefender_antsdr_scan.classification import SignalFeatures, classify_signal


class ControlConfidenceScalingTests(unittest.TestCase):
    def test_control_confidence_increases_with_hop_rate(self) -> None:
        low = classify_signal(
            SignalFeatures(
                freq_hz=915_000_000,
                band="915",
                snr_db=12.0,
                bandwidth_class="narrow",
                hop_rate_hz=1.0,
                burstiness=0.2,
            )
        )
        high = classify_signal(
            SignalFeatures(
                freq_hz=915_000_000,
                band="915",
                snr_db=12.0,
                bandwidth_class="narrow",
                hop_rate_hz=5.0,
                burstiness=0.2,
            )
        )
        self.assertEqual(low.class_path[:2], ["Control", "Hopping"])
        self.assertEqual(high.class_path[:2], ["Control", "Hopping"])
        self.assertGreater(high.confidence, low.confidence)

    def test_control_confidence_increases_with_burstiness(self) -> None:
        low = classify_signal(
            SignalFeatures(
                freq_hz=2_420_000_000,
                band="2G4",
                snr_db=12.0,
                bandwidth_class="narrow",
                burstiness=0.6,
                hop_rate_hz=0.0,
            )
        )
        high = classify_signal(
            SignalFeatures(
                freq_hz=2_420_000_000,
                band="2G4",
                snr_db=12.0,
                bandwidth_class="narrow",
                burstiness=0.9,
                hop_rate_hz=0.0,
            )
        )
        self.assertEqual(low.class_path[:2], ["Control", "Burst"])
        self.assertEqual(high.class_path[:2], ["Control", "Burst"])
        self.assertGreater(high.confidence, low.confidence)


if __name__ == "__main__":
    unittest.main()
