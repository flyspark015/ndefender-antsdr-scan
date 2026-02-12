import unittest

from ndefender_antsdr_scan.detectors.base import SpectrumFrame
from ndefender_antsdr_scan.detectors.peak import PeakDetector, PeakDetectorConfig


class PeakDetectorTests(unittest.TestCase):
    def test_detects_peak(self) -> None:
        detector = PeakDetector(PeakDetectorConfig(min_snr_db=5.0, lo_guard_hz=100.0))
        frame = SpectrumFrame(
            freqs_hz=[1.0, 2.0, 3.0, 4.0, 5.0],
            power_db=[1.0, 2.0, 10.0, 2.0, 1.0],
            timestamp_ms=0,
            band="test",
            lo_hz=None,
        )
        detections = detector.detect(frame)
        self.assertEqual(len(detections), 1)
        self.assertAlmostEqual(detections[0].freq_hz, 3.0)
        self.assertGreater(detections[0].snr_db, 5.0)

    def test_respects_lo_guard(self) -> None:
        detector = PeakDetector(PeakDetectorConfig(min_snr_db=5.0, lo_guard_hz=1.0))
        frame = SpectrumFrame(
            freqs_hz=[1.0, 2.0, 3.0],
            power_db=[1.0, 10.0, 1.0],
            timestamp_ms=0,
            band="test",
            lo_hz=2.0,
        )
        detections = detector.detect(frame)
        self.assertEqual(len(detections), 0)


if __name__ == "__main__":
    unittest.main()
