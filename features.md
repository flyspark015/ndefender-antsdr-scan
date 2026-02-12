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

## ✅ Band plan loading (analog 5.8 GHz)
- Description: Loads predefined analog 5.8 GHz band plans (RaceBand/FatShark/Band A) from YAML.
- Verification: `PYTHONPATH=src python -m unittest tests/test_plan_loading.py` → OK.

## ✅ Band plan loading (digital 5.8 GHz)
- Description: Loads predefined digital 5.8 GHz scan plan from YAML.
- Verification: `PYTHONPATH=src python -m unittest tests/test_plan_loading.py` → OK.

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
- Verification: `PYTHONPATH=src python -m unittest tests/test_cli_helpers.py` → OK. Dry-run: `PYTHONPATH=src python -m unittest tests/test_cli_run_dry.py` → OK. Replay e2e: `PYTHONPATH=src python -m unittest tests/test_cli_replay_e2e.py` → OK.

## ✅ CI workflow
- Description: GitHub Actions runs compile check, unit tests, and schema validation.
- Verification: See `.github/workflows/ci.yml` (pipeline configured).

## 🟡 In Progress — Advanced classification
- Description: Multi-level classification tree for analog/digital/control with confidence scoring.
- Verification: `PYTHONPATH=src python -m unittest tests/test_classification.py` → OK (rule-based stub, partially integrated).

## ✅ DSP feature extraction (bandwidth + burstiness)
- Description: Estimate bandwidth and burstiness for classification hints and control-link detection.
- Verification: `PYTHONPATH=src python -m unittest tests/test_dsp_features.py` → OK.

## ✅ Hop-rate estimation
- Description: Estimate hop rate over a rolling time window for control-link inference.
- Verification: `PYTHONPATH=src python -m unittest tests/test_hop_rate.py` → OK.

## ✅ Control-link rule classification (burst vs hopping)
- Description: Uses hop-rate and burstiness to label control signals as `Control/Hopping` or `Control/Burst`.
- Verification: `PYTHONPATH=src python -m unittest tests/test_classification_rules.py` → OK.

## ✅ Control-link scoring (burst + hop signal strength)
- Description: Scores control-likelihood using band, burstiness, and hop rate for confidence boosts.
- Verification: `PYTHONPATH=src python -m unittest tests/test_control_scoring.py` → OK.

## ✅ Profile-driven classification rules
- Description: Optional YAML profile rules to tag signals by frequency range, bandwidth class, and SNR.
- Verification: `PYTHONPATH=src python -m unittest tests/test_classification_profiles.py` → OK (closest-center selection).

## ✅ Correlation gating (video + control)
- Description: NEW event emitted only when control + video aligned within time window (configurable).
- Verification: `PYTHONPATH=src python -m unittest tests/test_correlation.py` → OK.

## ❌ Pending — Hardware validation
- Description: Live AntSDR capture validation, LO tuning checks, and WS emission.
- Verification: Not yet performed on target device.

---

# Detection & Tracking Capabilities (Drone RF)

Each detection type documents what we detect, how it is identified, output hints, and status.

## 🟡 Analog FPV VTX (5.8 GHz wideband FM)
- Detects: Wideband analog video carriers (common FPV VTX signals).
- Identification: Wide bandwidth peaks + low burstiness; optional profile match by band range.
- Output: Event `features.class_path` → ["Analog", "Video", "WideFM"], `classification_confidence`.
- Status: 🟡 In Progress (profile framework implemented; band-specific rules pending).
- Verification: `tests/test_classification_profiles.py` (synthetic profile), needs replay/soak for ✅.

## 🟡 RaceBand / FatShark / Band A channelization
- Detects: Specific analog band/channel edges (R1–R8, F1–F8, A/B/E).
- Identification: Band plan + channel center matching + stable FM plateau.
- Output: `features.class_path` includes channel/band tag; `pattern_hint` set.
- Status: 🟡 In Progress (profile rules implemented; field validation pending).
- Verification: `PYTHONPATH=src python -m unittest tests/test_classification_profiles_channels.py` → OK.

## 🟡 Digital FPV (OFDM-style bursts)
- Detects: Digital video links via OFDM-like PSD and burst timing.
- Identification: Burstiness + bandwidth estimate + OFDM signature.
- Output: `features.class_path` → ["Digital", "Video"], `pattern_hint`.
- Status: 🟡 In Progress (heuristic implemented; field validation pending).
- Verification: `PYTHONPATH=src python -m unittest tests/test_ofdm_signature.py` → OK.

## 🟡 DJI-specific (OcuSync/O3)
- Detects: Proprietary burst patterns + bandwidth constraints (non-encrypted inference only).
- Identification: OFDM signature + hop/burst patterns within DJI band window.
- Output: `features.class_path` includes "DJI" only if reliable; `encryption_hint` planned.
- Status: 🟡 In Progress (heuristic band-window tagging only).
- Verification: `PYTHONPATH=src python -m unittest tests/test_vendor_heuristics.py` → OK (heuristic only); `PYTHONPATH=src python -m unittest tests/test_vendor_profiles.py` → OK (profile placeholder + OFDM threshold).
  Schema: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid_vendor.jsonl` → validation ok.

## 🟡 Walksnail / HDZero
- Detects: Digital link signatures (bandwidth + burst rate profiles).
- Identification: OFDM signature + channel bandwidth.
- Output: `features.class_path` with vendor tag.
- Status: 🟡 In Progress (heuristic band-window tagging only).
- Verification: `PYTHONPATH=src python -m unittest tests/test_vendor_heuristics.py` → OK (heuristic only); `PYTHONPATH=src python -m unittest tests/test_vendor_profiles.py` → OK (profile placeholder + OFDM threshold).
  Schema: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid_vendor.jsonl` → validation ok.

## 🟡 ELRS / ExpressLRS (control link)
- Detects: Narrowband bursty control packets in 2.4/915 MHz.
- Identification: Narrowband peaks + burstiness + hop rate.
- Output: `features.class_path` → ["Control", "ELRS"], `pattern_hint`.
- Status: 🟡 In Progress (profile rule only; burst detection pending).
- Verification: `PYTHONPATH=src python -m unittest tests/test_control_profiles.py` → OK. Schema: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid_control.jsonl` → validation ok.

## 🟡 Crossfire / Tracer (control link)
- Detects: Narrowband control carriers in 915 MHz with hop patterns.
- Identification: Narrowband + hop detection + baud patterns (future).
- Output: `features.class_path` → ["Control", "Crossfire"].
- Status: 🟡 In Progress (profile rule + hop-rate signal; hop classification pending).
- Verification: `PYTHONPATH=src python -m unittest tests/test_control_profiles.py` → OK. Schema: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid_control.jsonl` → validation ok.

## ✅ Video + Control correlation gating
- Detects: Combined video + control alignment for higher confidence NEW.
- Identification: Timestamp correlation window (±100ms, configurable).
- Output: `features.control_correlation` true when correlated.
- Status: ✅ Implemented & Verified.
- Verification: `PYTHONPATH=src python -m unittest tests/test_correlation.py` → OK. Schema: `PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log tests/fixtures/valid_correlation.jsonl` → validation ok.
