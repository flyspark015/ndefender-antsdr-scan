import unittest

from ndefender_antsdr_scan.tracking.models import FeatureHints, Observation
from ndefender_antsdr_scan.tracking.tracker import Tracker, TrackerConfig


def _obs(ts_ms: int, class_path: list[str], freq_hz: float) -> Observation:
    features = FeatureHints(
        prominence_db=30.0,
        cluster_size=12,
        pattern_hint="unknown",
        hop_hint="none",
        class_path=class_path,
        classification_confidence=0.8,
    )
    return Observation(
        freq_hz=freq_hz,
        band="2G4" if freq_hz > 1_000_000_000 else "900",
        snr_db=30.0,
        peak_db=120.0,
        noise_floor_db=85.0,
        bandwidth_class="narrow",
        features=features,
        timestamp_ms=ts_ms,
    )


class CorrelationTests(unittest.TestCase):
    def test_correlation_gates_new(self) -> None:
        tracker = Tracker(
            TrackerConfig(
                bucket_hz=250000,
                ttl_s=120,
                min_hits_to_confirm=1,
                update_interval_s=1.0,
                correlation_enabled=True,
                correlation_window_ms=100,
            )
        )

        events = tracker.ingest([_obs(0, ["Analog", "Video"], 2_450_000_000)])
        self.assertEqual(len(events), 0)

        events = tracker.ingest([_obs(50, ["Control"], 915_000_000)])
        event_types = [event["type"] for event in events]
        self.assertEqual(event_types.count("RF_CONTACT_NEW"), 2)

    def test_no_correlation_required_when_disabled(self) -> None:
        tracker = Tracker(
            TrackerConfig(
                bucket_hz=250000,
                ttl_s=120,
                min_hits_to_confirm=1,
                update_interval_s=1.0,
                correlation_enabled=False,
                correlation_window_ms=100,
            )
        )
        events = tracker.ingest([_obs(0, ["Analog", "Video"], 2_450_000_000)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_NEW")


if __name__ == "__main__":
    unittest.main()
