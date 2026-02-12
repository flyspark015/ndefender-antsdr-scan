import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class ProfileConfidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("config/classification_profiles.yaml")
        self.classifier = Classifier(profiles=load_profiles(path))

    def test_analog_confidence_increases_with_snr(self) -> None:
        low = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_658_000_000,
                band="5G8",
                snr_db=12.0,
                bandwidth_class="wide",
                prominence_db=5.0,
            )
        )
        high = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_658_000_000,
                band="5G8",
                snr_db=30.0,
                bandwidth_class="wide",
                prominence_db=5.0,
            )
        )
        self.assertGreater(high.confidence, low.confidence)

    def test_analog_confidence_increases_with_prominence(self) -> None:
        low = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_855_000_000,
                band="5G8",
                snr_db=12.0,
                bandwidth_class="wide",
                prominence_db=2.0,
            )
        )
        high = self.classifier.classify(
            SignalFeatures(
                freq_hz=5_855_000_000,
                band="5G8",
                snr_db=12.0,
                bandwidth_class="wide",
                prominence_db=25.0,
            )
        )
        self.assertGreater(high.confidence, low.confidence)


if __name__ == "__main__":
    unittest.main()
