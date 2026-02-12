#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-config/default.yaml}"
MAX_FRAMES="${2:-5}"

PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main run --config "$CONFIG_PATH" --max-frames "$MAX_FRAMES"
PYTHONPATH=src python -m ndefender_antsdr_scan.cli.main validate --log /opt/ndefender/logs/antsdr_scan.jsonl
