import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class ControlProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("config/classification_profiles.yaml")
        profiles = load_profiles(path)
        self.classifier = Classifier(profiles=profiles)

    def test_elrs_2g4(self) -> None:
        features = SignalFeatures(
            freq_hz=2_445_000_000,
            band="2G4",
            snr_db=12.0,
            bandwidth_class="narrow",
        )
        result = self.classifier.classify(features)
        self.assertEqual(result.class_path, ["Control", "ELRS"])

    def test_crossfire_915(self) -> None:
        features = SignalFeatures(
            freq_hz=915_000_000,
            band="915",
            snr_db=12.0,
            bandwidth_class="narrow",
        )
        result = self.classifier.classify(features)
        self.assertEqual(result.class_path, ["Control", "Crossfire"])


if __name__ == "__main__":
    unittest.main()
