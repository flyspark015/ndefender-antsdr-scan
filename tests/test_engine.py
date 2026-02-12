import json
import os
import tempfile
import unittest

from ndefender_antsdr_scan.core.engine import ScanEngine
from ndefender_antsdr_scan.detectors.base import Detection, SpectrumFrame
from ndefender_antsdr_scan.io.emit import EventEmitter, EmitConfig
from ndefender_antsdr_scan.tracking.models import FeatureHints
from ndefender_antsdr_scan.tracking.tracker import Tracker, TrackerConfig


class _Detector:
    def __init__(self) -> None:
        self._features = FeatureHints(30.0, 12, "unknown", "none")

    def detect(self, frame: SpectrumFrame):
        return [
            Detection(
                freq_hz=2_450_000_000,
                band=frame.band,
                snr_db=30.0,
                peak_db=120.0,
                noise_floor_db=85.0,
                bandwidth_class="narrow",
                features=self._features,
            )
        ]


class EngineTests(unittest.TestCase):
    def test_engine_emits_and_logs(self) -> None:
        detector = _Detector()
        tracker = Tracker(
            TrackerConfig(bucket_hz=250000, ttl_s=120, min_hits_to_confirm=1, update_interval_s=1.0)
        )

        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "events.jsonl")
            emitter = EventEmitter(EmitConfig(jsonl_path=path))
            engine = ScanEngine(detector, tracker, emitter)

            frame = SpectrumFrame(
                freqs_hz=[1.0],
                power_db=[1.0],
                timestamp_ms=0,
                band="2G4",
                lo_hz=None,
            )
            events = engine.process_frame(frame)

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["type"], "RF_CONTACT_NEW")

            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["type"], "RF_CONTACT_NEW")


if __name__ == "__main__":
    unittest.main()
