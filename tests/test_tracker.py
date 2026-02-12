import unittest

from ndefender_antsdr_scan.events.validate import validate_event
from ndefender_antsdr_scan.tracking.models import FeatureHints, Observation
from ndefender_antsdr_scan.tracking.tracker import Tracker, TrackerConfig


def _features() -> FeatureHints:
    return FeatureHints(
        prominence_db=30.0,
        cluster_size=12,
        pattern_hint="unknown",
        hop_hint="none",
        class_path=["Analog", "Video"],
        classification_confidence=0.8,
        control_correlation=False,
    )


def _obs(ts_ms: int, snr_db: float = 30.0, freq_hz: float = 2_450_000_000) -> Observation:
    return Observation(
        freq_hz=freq_hz,
        band="2G4",
        snr_db=snr_db,
        peak_db=120.0,
        noise_floor_db=85.0,
        bandwidth_class="narrow",
        features=_features(),
        timestamp_ms=ts_ms,
    )


class TrackerLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = TrackerConfig(
            bucket_hz=250_000,
            ttl_s=120,
            min_hits_to_confirm=2,
            update_interval_s=1.0,
        )

    def test_new_then_update(self) -> None:
        tracker = Tracker(self.config)

        events = tracker.ingest([_obs(0)])
        self.assertEqual(len(events), 0)

        events = tracker.ingest([_obs(100)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_NEW")

        events = tracker.ingest([_obs(1500)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_UPDATE")

    def test_no_double_new(self) -> None:
        tracker = Tracker(self.config)

        tracker.ingest([_obs(0)])
        events = tracker.ingest([_obs(100)])
        self.assertEqual(events[0]["type"], "RF_CONTACT_NEW")

        events = tracker.ingest([_obs(200)])
        self.assertEqual(len(events), 0)

        events = tracker.ingest([_obs(1200)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_UPDATE")

    def test_ttl_expiry(self) -> None:
        tracker = Tracker(self.config)

        tracker.ingest([_obs(0)])
        tracker.ingest([_obs(100)])

        events = tracker.ingest([], now_ms=120_100)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_LOST")

        events = tracker.ingest([], now_ms=130_000)
        self.assertEqual(len(events), 0)

    def test_revisit_before_ttl(self) -> None:
        tracker = Tracker(self.config)

        tracker.ingest([_obs(0)])
        tracker.ingest([_obs(100)])

        events = tracker.ingest([_obs(50_000)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_UPDATE")

    def test_revisit_after_ttl(self) -> None:
        tracker = Tracker(self.config)

        tracker.ingest([_obs(0)])
        tracker.ingest([_obs(100)])

        events = tracker.ingest([], now_ms=121_000)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_LOST")

        events = tracker.ingest([_obs(122_000)])
        self.assertEqual(len(events), 0)

        events = tracker.ingest([_obs(122_100)])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "RF_CONTACT_NEW")

    def test_schema_validation(self) -> None:
        tracker = Tracker(self.config)
        tracker.ingest([_obs(0)])
        events = tracker.ingest([_obs(100)])
        self.assertEqual(len(events), 1)
        validate_event(events[0])


if __name__ == "__main__":
    unittest.main()
