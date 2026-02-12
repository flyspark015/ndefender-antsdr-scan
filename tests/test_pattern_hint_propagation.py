import unittest

from ndefender_antsdr_scan.classification import Classifier
from ndefender_antsdr_scan.classification.profiles import load_profiles
from ndefender_antsdr_scan.core.engine import ScanEngine
from ndefender_antsdr_scan.detectors.base import Detection
from ndefender_antsdr_scan.tracking.models import FeatureHints


class PatternHintPropagationTests(unittest.TestCase):
    def test_pattern_hint_flows_into_event(self) -> None:
        profiles = load_profiles("config/classification_profiles.yaml")
        engine = ScanEngine(
            detector=_NullDetector(),
            tracker=_NullTracker(),
            emitter=_NullEmitter(),
            classifier=Classifier(profiles=profiles),
        )
        detection = Detection(
            freq_hz=5_780_000_000,
            band="5G8",
            snr_db=20.0,
            peak_db=120.0,
            noise_floor_db=90.0,
            bandwidth_class="wide",
            features=FeatureHints(
                prominence_db=10.0,
                cluster_size=12,
                pattern_hint="unknown",
                hop_hint="none",
                bandwidth_est_hz=20_000_000,
                burstiness=0.4,
            ),
        )
        enriched = engine._augment_features(detection, timestamp_ms=123)
        self.assertEqual(enriched.pattern_hint, "dji_5g8")


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
