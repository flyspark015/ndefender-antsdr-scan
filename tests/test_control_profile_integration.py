import unittest

from ndefender_antsdr_scan.classification import Classifier
from ndefender_antsdr_scan.classification.profiles import load_profiles
from ndefender_antsdr_scan.core.engine import ScanEngine
from ndefender_antsdr_scan.detectors.base import Detection
from ndefender_antsdr_scan.tracking.models import FeatureHints


class ControlProfileIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        profiles = load_profiles("config/classification_profiles.yaml")
        self.engine = ScanEngine(
            detector=_NullDetector(),
            tracker=_NullTracker(),
            emitter=_NullEmitter(),
            classifier=Classifier(profiles=profiles),
        )

    def test_elrs_pattern_hint(self) -> None:
        detection = Detection(
            freq_hz=2_445_000_000,
            band="2G4",
            snr_db=12.0,
            peak_db=110.0,
            noise_floor_db=98.0,
            bandwidth_class="narrow",
            features=FeatureHints(
                prominence_db=5.0,
                cluster_size=4,
                pattern_hint="unknown",
                hop_hint="none",
                bandwidth_est_hz=200_000,
                burstiness=0.7,
            ),
        )
        features = self.engine._augment_features(detection, timestamp_ms=123)
        self.assertEqual(features.class_path, ["Control", "ELRS"])
        self.assertEqual(features.pattern_hint, "elrs_2g4")

    def test_crossfire_pattern_hint(self) -> None:
        detection = Detection(
            freq_hz=915_000_000,
            band="915",
            snr_db=12.0,
            peak_db=110.0,
            noise_floor_db=98.0,
            bandwidth_class="narrow",
            features=FeatureHints(
                prominence_db=5.0,
                cluster_size=4,
                pattern_hint="unknown",
                hop_hint="none",
                bandwidth_est_hz=200_000,
                burstiness=0.7,
            ),
        )
        features = self.engine._augment_features(detection, timestamp_ms=123)
        self.assertEqual(features.class_path, ["Control", "Crossfire"])
        self.assertEqual(features.pattern_hint, "crossfire_915")


class _NullDetector:
    def detect(self, frame):  # pragma: no cover - used for init only
        return []


class _NullTracker:
    def ingest(self, observations, now_ms=None):  # pragma: no cover - used for init only
        return []


class _NullEmitter:
    def emit_many(self, events):  # pragma: no cover - used for init only
        return None


if __name__ == "__main__":
    unittest.main()
