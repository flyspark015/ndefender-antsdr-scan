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
- Continuous sweep loop for live scanning (graceful shutdown)
- Configurable dwell pacing per sweep step
- Null-radio dry-run and max-frames guard for run loop
- README expanded with configuration and CLI guidance
- Classification module scaffold (rule-based)
- Classification enrichment in event features
- Correlation gating (video + control) with tests
- Profile-driven classification rules (YAML)
- Analog band/channel profile data (RaceBand/FatShark/Band A)
- Channel selection now prefers closest profile center frequency

## 🟡 What is currently in progress
- Live radio spectrum capture validation on hardware
- Advanced classification integration

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
- `PYTHONPATH=src python -m unittest tests/test_classification.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_engine.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_correlation.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_classification_profiles.py` → `OK`
- `PYTHONPATH=src python -m unittest tests/test_classification_profiles_channels.py` → `OK`

## 🧩 Test outcomes
- Tracker lifecycle tests: pass
- Peak detector tests: pass
- Sweep planner tests: pass
- Config loader tests: pass
- Engine wiring tests: pass
- CLI helper tests: pass
- Classification tests: pass
- Engine tests: pass (with classification hints)
- Correlation gating tests: pass
- Classification profile tests: pass
- Classification channel profile tests: pass
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
- `src/ndefender_antsdr_scan/core/config.py`
- `config/default.yaml`
- `tests/test_tracker.py`
- `tests/test_peak_detector.py`
- `tests/test_sweep.py`
- `tests/test_config.py`
- `tests/test_engine.py`
- `tests/test_cli_helpers.py`
- `tests/test_radio_spectrum.py`
- `src/ndefender_antsdr_scan/classification/engine.py`
- `src/ndefender_antsdr_scan/classification/models.py`
- `src/ndefender_antsdr_scan/classification/rules.py`
- `src/ndefender_antsdr_scan/core/engine.py`
- `src/ndefender_antsdr_scan/tracking/models.py`
- `src/ndefender_antsdr_scan/tracking/tracker.py`
- `src/ndefender_antsdr_scan/events/schema.json`
- `tests/test_classification.py`
- `tests/test_engine.py`
- `tests/test_cli_helpers.py`
- `features.md`
- `tests/test_correlation.py`
- `src/ndefender_antsdr_scan/classification/profiles.py`
- `tests/test_classification_profiles.py`
- `tests/fixtures/classification_profiles.yaml`
- `config/classification_profiles.yaml`
- `tests/test_classification_profiles_channels.py`
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
- Run loop validates sweep bands and handles graceful shutdown with flush
- Sweep pacing is configured via `sweep.dwell_ms` to control LO dwell time
- `run` supports `--null-radio` and `--max-frames` to enable safe dry runs
- Classification introduced as a separate module (rule-based stub) for staged integration
- Profile selection chooses closest center frequency to resolve overlapping channel bands

## ✅ Hardware validation checklist (planned)
- Verify AntSDR connectivity (`uri` reachable, `pyadi-iio` importable) — pending
- Confirm RX LO tuning across sweep band (start/stop/step behavior) — pending
- Validate FFT power spectrum shape and peak detection at known tones — pending
- Check event emission to JSONL at `/opt/ndefender/logs/antsdr_scan.jsonl` — pending
- Confirm WebSocket emission when enabled (connect/retry/backoff) — pending

## 🧪 Hardware validation commands (run on target device)
- `python -c "import adi; print(adi.__version__)"` (verify pyadi-iio import)
- `ndefender-antsdr-scan run --config config/default.yaml --max-frames 5` (live capture smoke test)
- `ndefender-antsdr-scan run --config config/default.yaml --null-radio --max-frames 5` (no-hardware dry run)
