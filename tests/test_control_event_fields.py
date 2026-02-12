import unittest

from ndefender_antsdr_scan.core.config import TrackerConfig
from ndefender_antsdr_scan.tracking.models import FeatureHints, Observation
from ndefender_antsdr_scan.tracking.tracker import Tracker


class ControlEventFieldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tracker = Tracker(
            TrackerConfig(
                bucket_hz=250_000,
                ttl_s=120,
                min_hits_to_confirm=1,
                update_interval_s=1.0,
                correlation_enabled=False,
                correlation_window_ms=200,
            )
        )

    def test_control_hopping_fields(self) -> None:
        ts = 1_700_000_000_000
        obs = Observation(
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
                class_path=["Control", "Hopping"],
                classification_confidence=0.85,
                control_correlation=False,
            ),
            timestamp_ms=ts,
        )
        events = self.tracker.ingest([obs], now_ms=ts)
        self.assertTrue(events)
        event = events[0]
        self.assertEqual(event["data"]["features"]["class_path"], ["Control", "Hopping"])
        self.assertEqual(event["data"]["features"]["classification_confidence"], 0.85)

    def test_control_burst_fields(self) -> None:
        ts = 1_700_000_000_100
        obs = Observation(
            freq_hz=2_420_000_000,
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
                class_path=["Control", "Burst"],
                classification_confidence=0.8,
                control_correlation=False,
            ),
            timestamp_ms=ts,
        )
        events = self.tracker.ingest([obs], now_ms=ts)
        self.assertTrue(events)
        event = events[0]
        self.assertEqual(event["data"]["features"]["class_path"], ["Control", "Burst"])
        self.assertEqual(event["data"]["features"]["classification_confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
