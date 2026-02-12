import unittest

from ndefender_antsdr_scan.classification import SignalFeatures, classify_signal
from ndefender_antsdr_scan.classification.ofdm import ofdm_signature_score


class OfdmSignatureTests(unittest.TestCase):
    def test_ofdm_score_high(self) -> None:
        features = SignalFeatures(
            freq_hz=5_800_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            bandwidth_est_hz=20_000_000,
            burstiness=0.5,
        )
        score = ofdm_signature_score(features)
        self.assertGreaterEqual(score, 0.7)

    def test_ofdm_classification(self) -> None:
        features = SignalFeatures(
            freq_hz=5_800_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            bandwidth_est_hz=20_000_000,
            burstiness=0.5,
        )
        result = classify_signal(features)
        self.assertEqual(result.class_path, ["Digital", "Video"])


if __name__ == "__main__":
    unittest.main()
