# N-Defender AntSDR Scan — Features

Each feature lists its current status and verification notes.

## ✅ Core scanning pipeline
- Description: RF sweep → peak detection → tracker lifecycle → JSONL emission.
- Verification: `PYTHONPATH=src python -m unittest tests/test_engine.py` → OK (emits events and logs).

## ✅ Tracker lifecycle & gating
- Description: Confirmation gating, update throttling, TTL expiry, and no double NEW without LOST.
- Verification: `PYTHONPATH=src python -m unittest tests/test_tracker.py` → OK.

## ✅ Peak detection (wideband FM)
- Description: Local maxima detection with LO guard and basic bandwidth classification.
- Verification: `PYTHONPATH=src python -m unittest tests/test_peak_detector.py` → OK.

## ✅ Sweep planning
- Description: Deterministic sweep step iterator with validation.
- Verification: `PYTHONPATH=src python -m unittest tests/test_sweep.py` → OK.

## ✅ Config loading
- Description: YAML config loader with sweep plans and WS config support.
- Verification: `PYTHONPATH=src python -m unittest tests/test_config.py` → OK.

## ✅ JSON schema validation
- Description: Validate event envelopes against canonical schema.
- Verification: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid.jsonl` → validation ok.

## ✅ FFT spectrum extraction
- Description: Converts IQ samples into frequency bins and power spectrum.
- Verification: `PYTHONPATH=src python -m unittest tests/test_radio_spectrum.py` → OK.

## ✅ CLI run/replay/stats
- Description: CLI entry points for live run, replay, validate, and stats.
- Verification: `PYTHONPATH=src python -m unittest tests/test_cli_helpers.py` → OK.

## ✅ CI workflow
- Description: GitHub Actions runs compile check, unit tests, and schema validation.
- Verification: See `.github/workflows/ci.yml` (pipeline configured).

## 🟡 In Progress — Advanced classification
- Description: Multi-level classification tree for analog/digital/control with confidence scoring.
- Verification: `PYTHONPATH=src python -m unittest tests/test_classification.py` → OK (rule-based stub, not integrated).

## ❌ Pending — Correlation gating (video + control)
- Description: NEW event emitted only when control + video aligned within time window.
- Verification: Not yet implemented.

## ❌ Pending — Hardware validation
- Description: Live AntSDR capture validation, LO tuning checks, and WS emission.
- Verification: Not yet performed on target device.
