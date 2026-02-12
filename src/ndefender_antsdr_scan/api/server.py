from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiohttp import web
import asyncio

from ndefender_antsdr_scan.api.bus import EventBus
from ndefender_antsdr_scan.api.runtime import EngineRunner
from ndefender_antsdr_scan.core.config import AppConfig, ApiConfig, load_config
from ndefender_antsdr_scan.version import __version__


@dataclass
class ApiState:
    config_path: Path
    config: AppConfig
    api_config: ApiConfig
    runner: EngineRunner
    event_bus: EventBus


APP_STATE = web.AppKey("state", ApiState)
APP_WS_CLIENTS = web.AppKey("ws_clients", set)


def _json_error(code: str, message: str, status: int = 400) -> web.Response:
    payload = {"error": {"code": code, "message": message}}
    return web.json_response(payload, status=status)


def _require_api_key(request: web.Request, api_key: str | None) -> web.Response | None:
    if not api_key:
        return None
    provided = request.headers.get("X-API-Key")
    if provided != api_key:
        return _json_error("unauthorized", "invalid API key", status=401)
    return None


@web.middleware
async def auth_middleware(request: web.Request, handler):
    state: ApiState = request.app[APP_STATE]
    error = _require_api_key(request, state.api_config.api_key)
    if error is not None:
        return error
    return await handler(request)


async def get_health(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    payload = {
        "status": "ok",
        "engine_running": state.runner.is_running,
        "ws_backend_connected": state.runner.ws_connected,
        "last_event_timestamp_ms": state.event_bus.last_timestamp_ms(),
        "timestamp_ms": int(time.time() * 1000),
    }
    return web.json_response(payload)


async def get_version(request: web.Request) -> web.Response:
    payload = {"version": __version__}
    return web.json_response(payload)


async def get_stats(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    stats = state.runner.stats
    if stats is None:
        payload = {"frames_processed": 0, "detections_processed": 0, "events_emitted": 0}
    else:
        payload = {
            "frames_processed": stats.frames_processed,
            "detections_processed": stats.detections_processed,
            "events_emitted": stats.events_emitted,
        }
    return web.json_response(payload)


async def get_config(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    config = state.config
    payload = {
        "radio": config.radio.__dict__,
        "tracker": config.tracker.__dict__,
        "detector": config.detector.__dict__,
        "sweep": {
            "bands": [band.__dict__ for band in config.sweep.bands],
            "dwell_ms": config.sweep.dwell_ms,
        },
        "ws": {
            "enabled": config.ws.enabled,
            "url": config.ws.url,
            "connect_timeout_s": config.ws.connect_timeout_s,
            "send_timeout_s": config.ws.send_timeout_s,
            "max_retries": config.ws.max_retries,
            "retry_backoff_s": config.ws.retry_backoff_s,
        },
        "classification": {
            "profiles": str(state.config_path.parent / "classification_profiles.yaml")
            if config.classification_profiles
            else "",
            "hop_window_ms": config.hop_window_ms,
            "min_hop_hz": config.min_hop_hz,
        },
        "api": {
            "enabled": state.api_config.enabled,
            "bind": state.api_config.bind,
            "port": state.api_config.port,
            "api_key": "***" if state.api_config.api_key else "",
            "max_clients": state.api_config.max_clients,
            "event_buffer": state.api_config.event_buffer,
        },
    }
    return web.json_response(payload)


async def post_config_reload(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    if state.runner.is_running:
        return _json_error("conflict", "cannot reload while running", status=409)
    state.config = load_config(state.config_path)
    state.api_config = state.config.api
    return web.json_response({"status": "ok"})


async def post_run_start(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    started = state.runner.start()
    if not started:
        return _json_error("conflict", "scan already running", status=409)
    return web.json_response({"status": "ok"})


async def post_run_stop(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    stopped = state.runner.stop()
    if not stopped:
        return _json_error("conflict", "scan not running", status=409)
    return web.json_response({"status": "ok"})


async def post_run_replay(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _json_error("bad_request", "invalid json")
    log_path = payload.get("log_path")
    if not log_path:
        return _json_error("bad_request", "missing log_path")
    if not Path(str(log_path)).exists():
        return _json_error("not_found", "log_path not found", status=404)
    output_path = payload.get("output_path")
    max_events = payload.get("max_events")
    max_events_val = int(max_events) if max_events is not None else None
    try:
        result = state.runner.replay(str(log_path), output_path=str(output_path) if output_path else None, max_events=max_events_val)
    except RuntimeError as exc:
        return _json_error("conflict", str(exc), status=409)
    return web.json_response({
        "status": "ok",
        "frames": result.frames,
        "detections": result.detections,
        "events_emitted": result.events_emitted,
    })


async def get_events_last(request: web.Request) -> web.Response:
    state: ApiState = request.app[APP_STATE]
    limit = int(request.query.get("limit", 50))
    return web.json_response({"events": state.event_bus.last(limit)})


async def ws_events(request: web.Request) -> web.StreamResponse:
    state: ApiState = request.app[APP_STATE]
    if state.api_config.api_key:
        provided = request.headers.get("X-API-Key")
        if provided != state.api_config.api_key:
            return _json_error("unauthorized", "invalid API key", status=401)
    if state.api_config.max_clients > 0:
        if len(request.app[APP_WS_CLIENTS]) >= state.api_config.max_clients:
            return _json_error("too_many_clients", "client limit reached", status=429)
    ws = web.WebSocketResponse(heartbeat=30.0)
    await ws.prepare(request)
    queue = state.event_bus.subscribe()
    request.app[APP_WS_CLIENTS].add(ws)
    try:
        while True:
            event = await queue.get()
            await ws.send_json(event)
    except Exception:
        return ws
    finally:
        state.event_bus.unsubscribe(queue)
        request.app[APP_WS_CLIENTS].discard(ws)


async def _on_startup(app: web.Application) -> None:
    state: ApiState = app[APP_STATE]
    state.event_bus.set_loop(asyncio.get_running_loop())


def create_app(state: ApiState) -> web.Application:
    app = web.Application(middlewares=[auth_middleware])
    app[APP_STATE] = state
    app[APP_WS_CLIENTS] = set()
    app.on_startup.append(_on_startup)

    app.router.add_get("/api/v1/health", get_health)
    app.router.add_get("/api/v1/version", get_version)
    app.router.add_get("/api/v1/stats", get_stats)
    app.router.add_get("/api/v1/config", get_config)
    app.router.add_post("/api/v1/config/reload", post_config_reload)
    app.router.add_post("/api/v1/run/start", post_run_start)
    app.router.add_post("/api/v1/run/stop", post_run_stop)
    app.router.add_post("/api/v1/run/replay", post_run_replay)
    app.router.add_get("/api/v1/events/last", get_events_last)
    app.router.add_get("/api/v1/events", ws_events)
    return app


def run_api_server(
    config_path: str,
    null_radio: bool = False,
    bind: str | None = None,
    port: int | None = None,
) -> int:
    config = load_config(config_path)
    api_config = config.api
    if not api_config.enabled:
        raise RuntimeError("api is disabled in config")
    event_bus = EventBus(maxlen=api_config.event_buffer)
    runner = EngineRunner(config, event_bus, null_radio=null_radio)
    state = ApiState(
        config_path=Path(config_path),
        config=config,
        api_config=api_config,
        runner=runner,
        event_bus=event_bus,
    )
    host = bind or api_config.bind
    port_val = port or api_config.port
    app = create_app(state)
    web.run_app(app, host=host, port=port_val)
    return 0
