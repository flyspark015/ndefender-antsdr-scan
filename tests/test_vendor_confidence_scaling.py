import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class VendorConfidenceScalingTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("config/classification_profiles.yaml")
        self.classifier = Classifier(profiles=load_profiles(path))

    def test_vendor_confidence_increases_with_ofdm_score(self) -> None:
        low = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_780_000_000,
                band="5G8",
                snr_db=18.0,
                bandwidth_class="wide",
                ofdm_score=0.72,
            )
        )
        high = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_780_000_000,
                band="5G8",
                snr_db=18.0,
                bandwidth_class="wide",
                ofdm_score=0.95,
            )
        )
        self.assertGreater(high.confidence, low.confidence)


if __name__ == "__main__":
    unittest.main()
