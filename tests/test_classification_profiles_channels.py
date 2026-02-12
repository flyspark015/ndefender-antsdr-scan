import unittest
from pathlib import Path

from ndefender_antsdr_scan.classification import Classifier, SignalFeatures
from ndefender_antsdr_scan.classification.profiles import load_profiles


class ClassificationProfileChannelTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("config/classification_profiles.yaml")
        self.profiles = load_profiles(path)
        self.classifier = Classifier(profiles=self.profiles)

    def _classify(self, freq_hz: float):
        return self.classifier.classify(
            SignalFeatures(
                freq_hz=freq_hz,
                band="5G8",
                snr_db=20.0,
                bandwidth_class="wide",
            )
        )

    def test_raceband_r1(self) -> None:
        result = self._classify(5_658_000_000)
        self.assertEqual(result.class_path[-1], "R1")

    def test_fatshark_f4(self) -> None:
        result = self._classify(5_780_000_000)
        self.assertEqual(result.class_path[-1], "F4")

    def test_banda_a8(self) -> None:
        result = self._classify(5_924_000_000)
        self.assertEqual(result.class_path[-1], "A8")


if __name__ == "__main__":
    unittest.main()
