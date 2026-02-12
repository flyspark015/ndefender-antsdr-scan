import json
import os
import subprocess
import sys
import tempfile
import unittest


class CliRunDryTests(unittest.TestCase):
    def test_run_null_radio_emits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "out.jsonl")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ndefender_antsdr_scan.cli.main",
                    "run",
                    "--config",
                    "config/default.yaml",
                    "--null-radio",
                    "--max-frames",
                    "2",
                    "--output",
                    out_path,
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": "src"},
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, "r", encoding="utf-8") as f:
                lines = [line for line in f if line.strip()]
            self.assertGreaterEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertIn(payload["type"], {"RF_CONTACT_NEW", "RF_CONTACT_UPDATE"})


if __name__ == "__main__":
    unittest.main()
