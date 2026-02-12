# N-Defender AntSDR RF Contact Detection & Tracking Engine

Modular AntSDR-based RF sweep, peak detection, contact tracking, lifecycle management, and JSON event emission engine for N-Defender.

Target: Raspberry Pi 5 (Python 3.11+)

## CLI

- `ndefender-antsdr-scan run --config config/default.yaml`
- `ndefender-antsdr-scan replay --log file.jsonl`
- `ndefender-antsdr-scan validate --log file.jsonl`
- `ndefender-antsdr-scan stats --log file.jsonl`
