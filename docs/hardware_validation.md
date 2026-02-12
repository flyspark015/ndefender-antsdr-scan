# Hardware Validation Guide (AntSDR)

This guide provides a repeatable checklist for validating live RF capture on an AntSDR device. It is designed to run on the target Raspberry Pi host with the AntSDR connected.

## Prerequisites
- AntSDR reachable at configured URI (default: `ip:192.168.10.2`).
- `pyadi-iio` installed and importable in the runtime environment.
- Project dependencies installed (`pip install -e .` or equivalent).

## Step 1 — Verify pyadi-iio import

Command:
```
python -c "import adi; print(adi.__version__)"
```

Expected:
- Prints a version string (non-empty).

## Step 2 — Basic dry-run (no hardware)

Command:
```
PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main run --config config/default.yaml --null-radio --max-frames 5
```

Expected:
- Exits successfully with no exceptions.

## Step 3 — Live capture smoke test

Command:
```
PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main run --config config/default.yaml --max-frames 5
```

Expected:
- Exits successfully after processing 5 frames.
- JSONL file written at `/opt/ndefender/logs/antsdr_scan.jsonl`.

## Step 4 — Validate JSONL output

Command:
```
PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log /opt/ndefender/logs/antsdr_scan.jsonl
```

Expected:
- `validation ok`.

## Step 5 — Replay validation

Command:
```
PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main replay --log /opt/ndefender/logs/antsdr_scan.jsonl --config config/default.yaml --output /tmp/replay.jsonl
```

Expected:
- Output JSONL created at `/tmp/replay.jsonl`.

## Notes
- If the AntSDR is not reachable, validate network/USB connectivity and confirm the correct URI in `config/default.yaml`.
- Use `--max-frames` for controlled, short runs.

