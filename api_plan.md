# API Plan — N-Defender AntSDR Scan

All items include a status checkbox. Use:
- ☐ Not started
- 🟡 In progress
- ✅ Implemented & verified

## API goals and scope ✅
- Provide stable, real-time delivery of RF events to external systems.
- Expose control, health, and stats endpoints for operations.
- Preserve existing backend WS contract and event schema.

## Architecture overview (modules + data flow) ✅
- Ingestion: `core/engine.py` produces events (JSON envelope).
- Emission: `io/emit.py` writes JSONL; WS client handles outbound to backend.
- API layer: new `api/server.py` exposes REST + WS for local integrations.
- Data flow: Engine → EventBus → JSONL + WS (backend) + API WS (local clients).

## Endpoints list (REST + WebSocket) ✅

### REST
- `GET /health` — liveness/readiness (engine status, ws status)
- `GET /version` — version info
- `GET /stats` — counters (frames/detections/events)
- `GET /config` — effective config (redact secrets)
- `POST /config/reload` — reload config from disk
- `POST /run/start` — start scan loop
- `POST /run/stop` — stop scan loop
- `POST /run/replay` — replay a JSONL file
- `GET /events/last` — last N events snapshot (for polling)

### WebSocket
- `WS /events` — stream RF event envelopes in real time

## Request/response schemas (with examples) ✅

### `GET /health`
Response:
```json
{
  "status": "ok",
  "engine_running": true,
  "ws_backend_connected": false,
  "timestamp_ms": 1700000000000
}
```

### `GET /stats`
Response:
```json
{
  "frames_processed": 100,
  "detections_processed": 1200,
  "events_emitted": 42
}
```

### `POST /run/replay`
Request:
```json
{
  "log_path": "/opt/ndefender/logs/antsdr_scan.jsonl",
  "output_path": "/tmp/replay.jsonl",
  "max_events": 100
}
```
Response:
```json
{
  "status": "ok",
  "events_emitted": 100
}
```

### `WS /events`
Message (already in canonical envelope):
```json
{
  "type": "RF_CONTACT_NEW",
  "timestamp": 1700000000000,
  "source": "antsdr",
  "data": {
    "id": "rf:2500000000",
    "freq_hz": 2500000000,
    "bucket_hz": 2500000000,
    "band": "2G4",
    "snr_db": 34.5,
    "bandwidth_class": "narrow",
    "confidence": 0.87,
    "features": {
      "pattern_hint": "raceband_r1"
    }
  }
}
```

## Authentication/authorization plan ✅
- API key header: `X-API-Key` (optional, configurable).
- Local-only binding by default (127.0.0.1).
- Future: token-based auth for multi-tenant deployments.

## Configuration requirements (env vars, ports, paths) ✅
- `API_ENABLED` (bool)
- `API_BIND` (host, default `127.0.0.1`)
- `API_PORT` (default `8890`)
- `API_KEY` (optional)
- `API_MAX_CLIENTS` (WS limit)
- `API_EVENT_BUFFER` (last N events)

## Error handling standards ✅
- JSON error envelope:
```json
{
  "error": {
    "code": "bad_request",
    "message": "missing log_path"
  }
}
```
- HTTP status codes: 200, 400, 401, 404, 409, 500.

## Versioning strategy ✅
- `/api/v1/*` prefix for REST.
- SemVer for package (`version.py`).
- Backward compatibility for WS event envelopes.

## Testing and verification plan ✅
- Unit tests for request validation and auth guard.
- Integration tests for start/stop/replay.
- WS streaming tests with mocked engine events.
- Schema validation for all emitted events.

## Deployment notes ✅
- Run via `ndefender-antsdr-scan api --config config/default.yaml`.
- Systemd service recommended for production.
- Ensure firewall rules for external binding.
