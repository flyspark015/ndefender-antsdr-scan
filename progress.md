# N-Defender AntSDR Scan — Progress

## ✅ What has been completed
- Project scaffold with `pyproject.toml`, CLI entry point, and default config
- JSON event schema and validation utilities
- Tracker lifecycle implementation with confirmation gating, update rate control, TTL expiry, and unit tests
- Backend contract helpers and JSONL emitter (default log path enforced)
- Peak detector and DSP helpers with unit tests
- Core sweep planner and radio interface stubs
- Config loader with YAML support
- Core scan engine wiring (detector → tracker → emitter)
- CLI run/replay/stats wiring (config-driven)
- Spectrum capture pipeline (FFT power spectrum + frequency bins)
- CI workflow (tests + schema validation + compile check)
- WebSocket client implementation with retry/backoff

## 🟡 What is currently in progress
- Live radio spectrum capture validation on hardware

## ❌ What is pending
- Production AntSDR capture pipeline (hardware tuning/testing)

## 🧪 Verification results
- `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log /tmp/antsdr_valid.jsonl` → `validation ok`
- `PYTHONPATH=src python -m unittest tests/test_tracker.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_peak_detector.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_sweep.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_config.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_engine.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_cli_helpers.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_radio_spectrum.py` → `OK`
- `PYTHONPATH=src python -m unittest discover -s tests` → `OK`

## 🧩 Test outcomes
- Tracker lifecycle tests: pass
- Peak detector tests: pass
- Sweep planner tests: pass
- Config loader tests: pass
- Engine wiring tests: pass
- CLI helper tests: pass
- Radio spectrum tests: pass

## 📦 Code changes implemented
- `src/ndefender_antsdr_scan/events/schema.json`
- `src/ndefender_antsdr_scan/events/validate.py`
- `src/ndefender_antsdr_scan/io/jsonl.py`
- `src/ndefender_antsdr_scan/tracking/models.py`
- `src/ndefender_antsdr_scan/tracking/tracker.py`
- `src/ndefender_antsdr_scan/api/contract.py`
- `src/ndefender_antsdr_scan/api/ws_client.py`
- `src/ndefender_antsdr_scan/io/emit.py`
- `src/ndefender_antsdr_scan/core/dsp.py`
- `src/ndefender_antsdr_scan/core/config.py`
- `src/ndefender_antsdr_scan/core/engine.py`
- `src/ndefender_antsdr_scan/core/radio.py`
- `src/ndefender_antsdr_scan/api/ws_client.py`
- `src/ndefender_antsdr_scan/core/sweep.py`
- `src/ndefender_antsdr_scan/detectors/base.py`
- `src/ndefender_antsdr_scan/detectors/peak.py`
- `src/ndefender_antsdr_scan/cli/helpers.py`
- `tests/test_tracker.py`
- `tests/test_peak_detector.py`
- `tests/test_sweep.py`
- `tests/test_config.py`
- `tests/test_engine.py`
- `tests/test_cli_helpers.py`
- `tests/test_radio_spectrum.py`
- `config/default.yaml`
- `pyproject.toml`
- `.github/workflows/ci.yml`
- `tests/fixtures/valid.jsonl`

## 🧠 Key decisions taken
- Enforced backend envelope schema via JSON Schema draft 2020-12
- Implemented confirmation gating to avoid premature NEW events
- Introduced update throttling and SNR delta triggers for UPDATE events
- Preserved default log path `/opt/ndefender/logs/antsdr_scan.jsonl`
- Added YAML-based config loader with optional plan file support
- CLI replay pass-throughs contact events; non-event records can be reconstructed into synthetic frames
- Implemented FFT-based spectrum extraction with windowing in `spectrum_from_samples`
- WebSocket client uses retry/backoff and JSON-encoded payloads
