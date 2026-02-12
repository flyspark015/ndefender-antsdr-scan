import unittest

from ndefender_antsdr_scan.core.sweep import BandPlan, iter_sweep


class SweepTests(unittest.TestCase):
    def test_iter_sweep_inclusive(self) -> None:
        bands = [BandPlan(name="2G4", start_hz=100.0, stop_hz=300.0, step_hz=100.0)]
        steps = list(iter_sweep(bands))
        self.assertEqual([s.lo_hz for s in steps], [100.0, 200.0, 300.0])

    def test_invalid_step(self) -> None:
        bands = [BandPlan(name="2G4", start_hz=100.0, stop_hz=200.0, step_hz=0.0)]
        with self.assertRaises(ValueError):
            list(iter_sweep(bands))


if __name__ == "__main__":
    unittest.main()
