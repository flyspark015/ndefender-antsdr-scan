import os
import tempfile
import unittest

from ndefender_antsdr_scan.cli.helpers import run_replay, run_stats
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


class CliHelperTests(unittest.TestCase):
    def test_run_stats_counts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "events.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    '{"type":"RF_CONTACT_NEW","timestamp":1,"source":"antsdr","data":{}}\n'
                )
                f.write(
                    '{"type":"RF_CONTACT_UPDATE","timestamp":2,"source":"antsdr","data":{}}\n'
                )
            stats = run_stats(path)

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["counts"]["RF_CONTACT_NEW"], 1)
        self.assertEqual(stats["counts"]["RF_CONTACT_UPDATE"], 1)
        self.assertEqual(stats["counts"]["RF_CONTACT_LOST"], 0)

    def test_run_replay_emits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            log_path = os.path.join(td, "input.jsonl")
            out_path = os.path.join(td, "output.jsonl")

            with open(log_path, "w", encoding="utf-8") as f:
                f.write(
                    '{"type":"RF_CONTACT_NEW","timestamp":1,"source":"antsdr","data":'
                    '{"freq_hz":2450000000,"peak_db":120.0,"band":"2G4"}}\n'
                )

            detector = _Detector()
            tracker = Tracker(
                TrackerConfig(bucket_hz=250000, ttl_s=120, min_hits_to_confirm=1, update_interval_s=1.0)
            )
            emitter = EventEmitter(EmitConfig(jsonl_path=out_path))
            engine = ScanEngine(detector, tracker, emitter)

            stats = run_replay(log_path, engine, emitter)
            self.assertEqual(stats["frames"], 0)
            self.assertEqual(stats["events_emitted"], 1)

            with open(out_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
