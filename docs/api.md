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
Returns counters for frames/detections/events.

### GET /config
Returns effective config (secrets redacted).

### POST /config/reload
Reloads config from disk (fails if scan running).

### POST /run/start
Starts live scan loop.

### POST /run/stop
Stops live scan loop.

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
  "error": {
    "code": "bad_request",
    "message": "missing log_path"
  }
}
```
