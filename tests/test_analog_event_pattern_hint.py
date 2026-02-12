import unittest

from ndefender_antsdr_scan.core.config import TrackerConfig
from ndefender_antsdr_scan.tracking.models import FeatureHints, Observation
from ndefender_antsdr_scan.tracking.tracker import Tracker


class AnalogEventPatternHintTests(unittest.TestCase):
    def test_analog_pattern_hint_in_event(self) -> None:
        tracker = Tracker(
            TrackerConfig(
                bucket_hz=250_000,
                ttl_s=120,
                min_hits_to_confirm=1,
                update_interval_s=1.0,
                correlation_enabled=False,
                correlation_window_ms=200,
            )
        )
        ts = 1_700_000_000_000
        obs = Observation(
            freq_hz=5_658_000_000,
            band="5G8",
            snr_db=20.0,
            peak_db=120.0,
            noise_floor_db=90.0,
            bandwidth_class="wide",
            features=FeatureHints(
                prominence_db=10.0,
                cluster_size=12,
                pattern_hint="raceband_r1",
                hop_hint="none",
                class_path=["Analog", "Video", "RaceBand", "R1"],
                classification_confidence=0.9,
                control_correlation=False,
            ),
            timestamp_ms=ts,
        )
        events = tracker.ingest([obs], now_ms=ts)
        self.assertTrue(events)
        event = events[0]
        features = event["data"]["features"]
        self.assertEqual(features["pattern_hint"], "raceband_r1")
        self.assertEqual(features["class_path"], ["Analog", "Video", "RaceBand", "R1"])


if __name__ == "__main__":
    unittest.main()
