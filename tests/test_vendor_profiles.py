import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class VendorProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("config/classification_profiles.yaml")
        profiles = load_profiles(path)
        self.classifier = Classifier(profiles=profiles)

    def test_dji_profile(self) -> None:
        features = SignalFeatures(
            freq_hz=5_780_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            ofdm_score=0.8,
        )
        result = self.classifier.classify(features)
        self.assertEqual(result.class_path, ["Digital", "Video", "DJI"])

    def test_walksnail_profile(self) -> None:
        features = SignalFeatures(
            freq_hz=5_890_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            ofdm_score=0.8,
        )
        result = self.classifier.classify(features)
        self.assertEqual(result.class_path, ["Digital", "Video", "Walksnail"])

    def test_hdzero_profile(self) -> None:
        features = SignalFeatures(
            freq_hz=5_650_000_000,
            band="5G8",
            snr_db=15.0,
            bandwidth_class="wide",
            ofdm_score=0.8,
        )
        result = self.classifier.classify(features)
        self.assertEqual(result.class_path, ["Digital", "Video", "HDZero"])


if __name__ == "__main__":
    unittest.main()
