import unittest

from ndefender_antsdr_scan.classification.scoring import score_control
from ndefender_antsdr_scan.classification import SignalFeatures


class ControlScoringTests(unittest.TestCase):
    def test_control_score_high(self) -> None:
        features = SignalFeatures(
            freq_hz=915_000_000,
            band="915",
            snr_db=12.0,
            bandwidth_class="narrow",
            burstiness=0.7,
            hop_rate_hz=3.0,
        )
        score = score_control(features)
        self.assertGreaterEqual(score, 0.8)

    def test_control_score_low(self) -> None:
        features = SignalFeatures(
            freq_hz=5_800_000_000,
            band="5G8",
            snr_db=20.0,
            bandwidth_class="wide",
            burstiness=0.1,
            hop_rate_hz=0.0,
        )
        score = score_control(features)
        self.assertLessEqual(score, 0.2)


if __name__ == "__main__":
    unittest.main()
