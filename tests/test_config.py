import tempfile
import unittest
from pathlib import Path

from ndefender_antsdr_scan.core.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_minimal_config(self) -> None:
        content = """
radio:
  uri: "ip:192.168.10.2"
  sample_rate: 2000000
tracker:
  bucket_hz: 250000
  ttl_s: 120
  min_hits_to_confirm: 2
  update_interval_s: 1.0
detector:
  min_snr_db: 10
  lo_guard_hz: 100000
"""
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "config.yaml"
            path.write_text(content, encoding="utf-8")
            cfg = load_config(path)

        self.assertEqual(cfg.radio.uri, "ip:192.168.10.2")
        self.assertEqual(cfg.radio.sample_rate, 2000000)
        self.assertEqual(cfg.tracker.bucket_hz, 250000)
        self.assertEqual(cfg.tracker.ttl_s, 120)
        self.assertEqual(cfg.detector.min_snr_db, 10)
        self.assertEqual(cfg.sweep.bands, [])
        self.assertFalse(cfg.ws.enabled)
        self.assertEqual(cfg.ws.url, "")
        self.assertIsNone(cfg.classification_profiles)
        self.assertEqual(cfg.hop_window_ms, 1000)
        self.assertEqual(cfg.min_hop_hz, 200000.0)


if __name__ == "__main__":
    unittest.main()
