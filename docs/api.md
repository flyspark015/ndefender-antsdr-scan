# API Reference (v1)

Base path: `/api/v1`

## Authentication
If `api.api_key` is set, include `X-API-Key` header.

## Endpoints

### GET /health
Returns status and engine state.

Response includes:
- `last_event_timestamp_ms` (null if no events published)

### GET /version
Returns package version.

### GET /stats
Returns counters for frames/events.

### GET /device
Returns AntSDR device connectivity and URI.

### GET /sweep/state
Returns sweep plans and running state.

### GET /gain
Returns current gain mode (auto/manual).

### GET /config
Returns effective config (secrets redacted).

### POST /config/reload
Reloads config from disk (fails if scan running).

### POST /run/start
Starts live scan loop (legacy).

### POST /run/stop
Stops live scan loop (legacy).

### POST /sweep/start
Starts sweep using the selected plan.

Request:
```json
{"payload":{"plan":"default"},"confirm":false}
```

### POST /sweep/stop
Stops sweep.

Request:
```json
{"payload":{},"confirm":false}
```

### POST /gain/set
Set gain mode.

Request:
```json
{"payload":{"mode":"auto","gain_db":null},"confirm":false}
```

### POST /device/reset
Dangerous reset (confirm required).

Request:
```json
{"payload":{},"confirm":true}
```

### POST /device/calibrate
Dangerous calibration (confirm required).

Request:
```json
{"payload":{"kind":"rf_dc"},"confirm":true}
```

### POST /run/replay
Replay a JSONL log into the pipeline.

Request:
```json
{
  "log_path": "/opt/ndefender/logs/antsdr_scan.jsonl",
  "output_path": "/tmp/replay.jsonl",
  "max_events": 100
}
```

Errors:
- `404 not_found` if `log_path` does not exist.

### GET /events/last?limit=50
Returns the last N events as a snapshot.

### WS /events
WebSocket stream of RF event envelopes.

## Error format
```json
{
  "detail": "missing_log_path"
}
```

## Monitoring

Use the automated API monitor to verify health, stream events, and track classifications in real time:

```bash
./tools/api_monitor.py --url http://127.0.0.1:8890
```

One-shot API self-test:

```bash
./tools/api_monitor.py --url http://127.0.0.1:8890 --self-test
```
