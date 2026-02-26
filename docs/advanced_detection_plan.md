# Advanced Detection Plan (Ultra-Deep RF Classification)

This plan describes how we will implement the requested multi-level FPV RF classification and detection logic in the new modular engine without breaking the backend contract. It is structured to map requirements to modules, configs, event fields, and tests.

## Goals
- Add multi-level classification for analog, digital, and control links.
- Use passive RF sniffing only (sweep, peaks, SNR, burstiness, hop rate, OFDM heuristics).
- Avoid false NEW/UPDATE events via confirmation gating and correlation gating.
- Keep backend envelope and schema stable; only optional feature fields may grow.
- Make rules data-driven so new bands/protocols are added via YAML, not code.

## Non-Goals
- No decryption or payload decode.
- No active transmission.
- No vendor-specific claims unless heuristic thresholds are met.

## Architecture Mapping

### Modules and Responsibilities
- `src/ndefender_antsdr_scan/core/sweep.py`
  - Use plan files per band/protocol.
  - Support multi-plan rotation (analog 5.8, digital 5.8, control 2.4/915).

- `src/ndefender_antsdr_scan/detectors/peak.py`
  - Produce candidates with peak power, SNR, prominence, and bandwidth class.

- `src/ndefender_antsdr_scan/core/dsp.py`
  - Add advanced features: bandwidth estimate, burstiness, plateau stability.

- `src/ndefender_antsdr_scan/core/hopping.py`
  - Estimate hop rate and variability.

- `src/ndefender_antsdr_scan/classification/profiles.py`
  - YAML-driven profile selection (band ranges, bandwidth class, SNR).
  - Priority rules for vendor tags.

- `src/ndefender_antsdr_scan/classification/rules.py`
  - Rule-based inference (Analog vs Digital vs Control).
  - OFDM heuristic; control burst/hopping detection.

- `src/ndefender_antsdr_scan/classification/engine.py`
  - Merge profile and rule outputs into `class_path` and `classification_confidence`.

- `src/ndefender_antsdr_scan/tracking/tracker.py`
  - Confirmation gating for NEW.
  - UPDATE throttling and SNR delta trigger.
  - TTL-based LOST.

- `src/ndefender_antsdr_scan/events/schema.json`
  - Keep envelope fixed.
  - Extend only optional `features.*` fields.

## Detection Tree Implementation Plan

### 1) Analog FPV (5.8 GHz wideband FM)
- Data inputs: bandwidth estimate, burstiness, prominence.
- Rule: wide bandwidth + low burstiness + 5.8 band.
- Output: `features.class_path = ["Analog", "Video", "WideFM"]`.
- Profiles: RaceBand/FatShark/Band A in `config/classification_profiles.yaml`.
- Confidence: scale by SNR and prominence.

### 2) Analog Channelization (RaceBand/FatShark/Band A)
- Data inputs: closest center frequency match, stable plateau.
- Rule: frequency within channel window; choose closest center.
- Output: `features.pattern_hint = "raceband_r1"` (example), `features.class_path` extended.
- Config: channel maps in `config/classification_profiles.yaml`.

### 3) Digital FPV (OFDM-like)
- Data inputs: OFDM signature, burstiness, bandwidth.
- Rule: OFDM score >= threshold; 5.8 band.
- Output: `features.class_path = ["Digital", "Video"]`.
- Confidence: combine OFDM score + SNR.

### 4) Vendor Hints (DJI / Walksnail / HDZero)
- Data inputs: OFDM score, band window, bandwidth.
- Rule: require OFDM score >= 0.7 and matching vendor window.
- Output: `features.class_path` extended with vendor tag.
- Config: vendor priority in `config/classification_profiles.yaml`.

### 5) Control Links (2.4 / 915 MHz)
- Data inputs: narrow bandwidth, burstiness, hop rate.
- Rule: high burstiness OR detectable hop rate.
- Output: `features.class_path = ["Control", "Burst"]` or `["Control", "Hopping"]`.
- Profiles: ELRS, Crossfire/Tracer in `config/classification_profiles.yaml`.

### 6) Correlation Gating (Video + Control)
- Data inputs: temporal alignment of control and video contacts.
- Rule: emit NEW only if correlated in configurable window.
- Output: `features.control_correlation = true` when correlated.

## Configuration Plan

- `config/default.yaml`
  - Add/confirm sweep plans for analog/digital 5.8 and control 2.4/915.
  - Track correlation config and classification thresholds.

- `config/plans/`
  - `analog_5g8.yaml`, `digital_5g8.yaml`, `control_2g4.yaml`, `control_915.yaml`.

- `config/classification_profiles.yaml`
  - Analog channel definitions, vendor profiles, control link profiles.

## Event Output Plan (No Contract Breaks)

Envelope stays fixed:
- `type`, `timestamp_ms`, `source`, `data`.

Feature fields (optional):
- `class_path` (list)
- `classification_confidence` (float)
- `control_correlation` (bool)
- `hop_rate_hz` (float)
- `burstiness` (float)
- `bandwidth_est_hz` (float)
- `pattern_hint`, `encryption_hint` (strings, optional)

All fields must pass schema validation.

## Testing Plan

Unit tests:
- Profile selection (closest center, priority).
- OFDM heuristic (positive/negative).
- Control burst vs hopping classification.
- Correlation gating behavior.

Fixtures:
- JSONL fixtures for vendor/control/correlation schema validation.

CLI:
- Replay e2e test to ensure replay emits valid events.
- Dry-run test for live run with null radio.

## Phased Implementation

Phase 1 (Rules + Profiles)
- Expand profile rules for analog channels and control link types.
- Implement OFDM threshold gating for vendor tags.

Phase 2 (Advanced Features)
- Add improved burstiness and bandwidth estimation.
- Add hop-rate estimation in rolling window.

Phase 3 (Correlation + Confidence)
- Enhance correlation gating and confidence scaling.

Phase 4 (Hardware Validation)
- Validate sweep performance and event emission on AntSDR.

## Risks and Mitigations
- False vendor tags: require OFDM threshold + profile match.
- Excess NEW events: rely on confirmation gating and correlation.
- Band overlap: priority order and closest-center rules.
