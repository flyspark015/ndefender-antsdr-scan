import unittest

from ndefender_antsdr_scan.classification import SignalFeatures, classify_signal


class OFDMConfidenceScalingTests(unittest.TestCase):
    def test_confidence_increases_with_ofdm_score(self) -> None:
        low = classify_signal(
            SignalFeatures(
                freq_hz=5_950_000_000,
                band="5G8",
                snr_db=15.0,
                bandwidth_class="wide",
                bandwidth_est_hz=8_000_000,
                burstiness=0.2,
            )
        )
        high = classify_signal(
            SignalFeatures(
                freq_hz=5_950_000_000,
                band="5G8",
                snr_db=25.0,
                bandwidth_class="wide",
                bandwidth_est_hz=25_000_000,
                burstiness=0.5,
            )
        )
        self.assertEqual(low.class_path[:2], ["Digital", "Video"])
        self.assertEqual(high.class_path[:2], ["Digital", "Video"])
        self.assertGreater(high.confidence, low.confidence)


if __name__ == "__main__":
    unittest.main()
