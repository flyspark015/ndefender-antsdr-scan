import os
import subprocess
import sys
import unittest
from pathlib import Path


class SchemaFixtureTests(unittest.TestCase):
    def test_all_fixtures_validate(self) -> None:
        fixtures = [
            "tests/fixtures/valid.jsonl",
            "tests/fixtures/valid_vendor.jsonl",
            "tests/fixtures/valid_control.jsonl",
            "tests/fixtures/valid_correlation.jsonl",
        ]
        for fixture in fixtures:
            env = {**os.environ, "PYTHONPATH": "src"}
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ndefender_antsdr_scan.cli.main",
                    "validate",
                    "--log",
                    fixture,
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
