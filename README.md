# N-Defender AntSDR RF Contact Detection & Tracking Engine

Modular AntSDR-based RF sweep, peak detection, contact tracking, lifecycle management, and JSON event emission engine for N-Defender.

Target: Raspberry Pi 5 (Python 3.11+)

## Requirements

- Python 3.11+
- AntSDR (AD9364) for live capture
- `pyadi-iio` installed for hardware access

## Install

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

## Configuration

Default config: `config/default.yaml`

Example sweep configuration:

```yaml
radio:
  uri: "ip:192.168.10.2"
  sample_rate: 2000000
  rx_buffer_size: 4096

tracker:
  bucket_hz: 250000
  ttl_s: 120
  min_hits_to_confirm: 2
  update_interval_s: 1.0

detector:
  min_snr_db: 10
  lo_guard_hz: 100000

sweep:
  dwell_ms: 0
  bands:
    - name: "2G4"
      start_hz: 2400000000
      stop_hz: 2485000000
      step_hz: 2000000

ws:
  enabled: false
  url: ""
  connect_timeout_s: 5.0
  send_timeout_s: 2.0
  max_retries: 3
  retry_backoff_s: 1.0

classification:
  profiles: ""
api:
  enabled: false
  bind: "127.0.0.1"
  port: 8890
  api_key: ""
  max_clients: 25
  event_buffer: 500
```

Logs are written to:

```
/opt/ndefender/logs/antsdr_scan.jsonl
```

Production integration:
- The Backend Aggregator tails `/opt/ndefender/logs/antsdr_scan.jsonl` for RF status + contacts.
- If the AntSDR is unreachable (e.g., `ip:192.168.10.2` not reachable), the JSONL will not update and the API reports `rf.status=offline` with `last_error=antsdr_unreachable`.
- Recommended systemd backoff (to reduce restart storms):
  - `RestartSec=5`
  - `StartLimitIntervalSec=60`
  - `StartLimitBurst=6`

## CLI

Run live scan:

```bash
ndefender-antsdr-scan run --config config/default.yaml
```

Optional: add a classification profile file and set `classification.profiles` to enable profile-driven tagging.

Dry-run without hardware (null radio) and stop after N frames:

```bash
ndefender-antsdr-scan run --config config/default.yaml --null-radio --max-frames 5
```

Replay an existing JSONL log:

```bash
ndefender-antsdr-scan replay --log file.jsonl --config config/default.yaml
```

Validate a JSONL log against the event schema:

```bash
ndefender-antsdr-scan validate --log file.jsonl
```

Quick stats from a JSONL log:

```bash
ndefender-antsdr-scan stats --log file.jsonl
```

## API

Enable the API in `config/default.yaml` (`api.enabled: true`), then run:

```bash
ndefender-antsdr-scan api --config config/default.yaml
```

See `docs/api.md` for endpoints and examples.

Environment overrides:
- `API_ENABLED`
- `API_BIND`
- `API_PORT`
- `API_KEY`
- `API_MAX_CLIENTS`
- `API_EVENT_BUFFER`

## Monitoring Dashboard

Run the automated API monitor (dashboard + self-test):

```bash
./tools/api_monitor.py --url http://127.0.0.1:8890
```

One-shot test mode:

```bash
./tools/api_monitor.py --url http://127.0.0.1:8890 --self-test
```

## Development

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Hardware Validation (AntSDR)

See `docs/hardware_validation.md` for a step-by-step checklist and smoke test workflow.
