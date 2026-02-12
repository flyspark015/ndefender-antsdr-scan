import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class ClassificationProfileTests(unittest.TestCase):
    def test_profile_match(self) -> None:
        path = Path("tests/fixtures/classification_profiles.yaml")
        profiles = load_profiles(path)
        classifier = Classifier(profiles=profiles)
        features = SignalFeatures(
            freq_hz=5_700_000_000,
            band="5G8",
            snr_db=20.0,
            bandwidth_class="wide",
        )
        result = classifier.classify(features)
        self.assertEqual(result.class_path[-1], "RaceBand")
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_profile_rejects_low_snr(self) -> None:
        path = Path("tests/fixtures/classification_profiles.yaml")
        profiles = load_profiles(path)
        classifier = Classifier(profiles=profiles)
        features = SignalFeatures(
            freq_hz=5_700_000_000,
            band="5G8",
            snr_db=5.0,
            bandwidth_class="wide",
        )
        result = classifier.classify(features)
        self.assertNotEqual(result.class_path[-1], "RaceBand")


if __name__ == "__main__":
    unittest.main()
