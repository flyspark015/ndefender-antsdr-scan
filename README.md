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
```

Logs are written to:

```
/opt/ndefender/logs/antsdr_scan.jsonl
```

## CLI

Run live scan:

```bash
ndefender-antsdr-scan run --config config/default.yaml
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

## Development

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
