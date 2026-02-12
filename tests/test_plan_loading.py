import unittest
from pathlib import Path

from ndefender_antsdr_scan.core.config import load_config


class PlanLoadingTests(unittest.TestCase):
    def test_plan_loading(self) -> None:
        path = Path("config/default.yaml")
        config = load_config(path)
        self.assertGreaterEqual(len(config.sweep.bands), 3)
        names = {band.name for band in config.sweep.bands}
        self.assertIn("5G8_RaceBand", names)
        self.assertIn("5G8_FatShark", names)
        self.assertIn("5G8_BandA", names)


if __name__ == "__main__":
    unittest.main()
