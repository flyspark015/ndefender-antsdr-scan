import unittest

from ndefender_antsdr_scan.core.config import TrackerConfig
from ndefender_antsdr_scan.tracking.models import FeatureHints, Observation
from ndefender_antsdr_scan.tracking.tracker import Tracker


class CorrelationEventFieldTests(unittest.TestCase):
    def test_control_correlation_preserved(self) -> None:
        tracker = Tracker(
            TrackerConfig(
                bucket_hz=250_000,
                ttl_s=120,
                min_hits_to_confirm=1,
                update_interval_s=1.0,
                correlation_enabled=True,
                correlation_window_ms=200,
            )
        )
        ts = 1_700_000_000_000
        video_obs = Observation(
            freq_hz=5_800_000_000,
            band="5G8",
            snr_db=20.0,
            peak_db=120.0,
            noise_floor_db=90.0,
            bandwidth_class="wide",
            features=FeatureHints(
                prominence_db=10.0,
                cluster_size=12,
                pattern_hint="raceband_r5",
                hop_hint="none",
                class_path=["Analog", "Video", "RaceBand", "R5"],
                classification_confidence=0.9,
                control_correlation=False,
            ),
            timestamp_ms=ts,
        )
        control_obs = Observation(
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
                classification_confidence=0.8,
                control_correlation=True,
            ),
            timestamp_ms=ts + 50,
        )
        events = tracker.ingest([video_obs, control_obs], now_ms=ts)
        self.assertTrue(any(e["type"] == "RF_CONTACT_NEW" for e in events))
        correlated = [e for e in events if e["data"]["features"].get("control_correlation")]
        self.assertTrue(correlated)


if __name__ == "__main__":
    unittest.main()
