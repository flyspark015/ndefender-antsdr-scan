#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Deque

import aiohttp


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_CYAN = "\033[36m"
ANSI_GRAY = "\033[90m"


@dataclass
class ApiMetrics:
    ok: int = 0
    fail: int = 0
    last_latency_ms: float | None = None
    avg_latency_ms: float | None = None


@dataclass
class MonitorState:
    base_url: str
    api_key: str | None
    start_time: float = field(default_factory=time.time)
    connected: bool = False
    ws_connected: bool = False
    health_ok: bool = False
    last_event_ts: int | None = None
    last_error: str | None = None
    unique_ids: set[str] = field(default_factory=set)
    class_map: dict[str, str] = field(default_factory=dict)
    class_counts: Counter = field(default_factory=Counter)
    event_counts: Counter = field(default_factory=Counter)
    api_metrics: ApiMetrics = field(default_factory=ApiMetrics)
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=12))

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")


def _color(text: str, color: str) -> str:
    return f"{color}{text}{ANSI_RESET}"


def _status_icon(ok: bool) -> str:
    return "✅" if ok else "❌"


def _ws_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.startswith("https://"):
        return "wss://" + url[len("https://") :] + "/api/v1/events"
    if url.startswith("http://"):
        return "ws://" + url[len("http://") :] + "/api/v1/events"
    return "ws://" + url + "/api/v1/events"


def _api_base(base_url: str) -> str:
    return base_url.rstrip("/") + "/api/v1"


async def _fetch_json(session: aiohttp.ClientSession, url: str, headers: dict[str, str]) -> tuple[bool, dict | None, float]:
    start = time.time()
    try:
        async with session.get(url, headers=headers, timeout=5) as resp:
            latency_ms = (time.time() - start) * 1000.0
            if resp.status != 200:
                return False, None, latency_ms
            payload = await resp.json()
            return True, payload, latency_ms
    except Exception:
        latency_ms = (time.time() - start) * 1000.0
        return False, None, latency_ms


async def _post_json(
    session: aiohttp.ClientSession, url: str, headers: dict[str, str], payload: dict
) -> tuple[bool, dict | None]:
    try:
        async with session.post(url, headers=headers, json=payload, timeout=10) as resp:
            if resp.status != 200:
                return False, None
            return True, await resp.json()
    except Exception:
        return False, None


async def run_self_test(base_url: str, api_key: str | None, ws_check: bool = True) -> dict[str, bool]:
    headers = {"X-API-Key": api_key} if api_key else {}
    api_base = _api_base(base_url)
    results = {}
    async with aiohttp.ClientSession() as session:
        ok, _payload, _lat = await _fetch_json(session, f"{api_base}/health", headers)
        results["health"] = ok
        ok, _payload, _lat = await _fetch_json(session, f"{api_base}/stats", headers)
        results["stats"] = ok
        ok, _payload, _lat = await _fetch_json(session, f"{api_base}/config", headers)
        results["config"] = ok
        ok, _payload, _lat = await _fetch_json(session, f"{api_base}/events/last?limit=1", headers)
        results["events_last"] = ok

        if ws_check:
            ws_url = _ws_url(base_url)
            try:
                async with session.ws_connect(ws_url, headers=headers, timeout=5):
                    results["ws"] = True
            except Exception:
                results["ws"] = False
    return results


async def _poll_health(state: MonitorState, interval_s: float) -> None:
    headers = {"X-API-Key": state.api_key} if state.api_key else {}
    api_base = _api_base(state.base_url)
    async with aiohttp.ClientSession() as session:
        while True:
            ok, payload, latency_ms = await _fetch_json(session, f"{api_base}/health", headers)
            state.api_metrics.last_latency_ms = latency_ms
            if ok:
                state.api_metrics.ok += 1
                if state.api_metrics.avg_latency_ms is None:
                    state.api_metrics.avg_latency_ms = latency_ms
                else:
                    state.api_metrics.avg_latency_ms = (
                        state.api_metrics.avg_latency_ms * 0.8 + latency_ms * 0.2
                    )
                state.health_ok = True
                state.connected = True
                if payload:
                    state.last_event_ts = payload.get("last_event_timestamp_ms")
            else:
                state.api_metrics.fail += 1
                state.health_ok = False
            await asyncio.sleep(interval_s)


async def _consume_events(state: MonitorState) -> None:
    headers = {"X-API-Key": state.api_key} if state.api_key else {}
    ws_url = _ws_url(state.base_url)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.ws_connect(ws_url, headers=headers, timeout=10) as ws:
                    state.ws_connected = True
                    state.log("🔌 API connected (WS)")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                event = json.loads(msg.data)
                            except json.JSONDecodeError:
                                state.log("⚠️  invalid event JSON")
                                continue
                            _handle_event(state, event)
                        elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                            break
            except Exception as exc:
                state.ws_connected = False
                state.last_error = str(exc)
                state.log(f"⚠️  WS error: {exc}")
                await asyncio.sleep(2.0)


def _handle_event(state: MonitorState, event: dict) -> None:
    event_type = event.get("type")
    if event_type:
        state.event_counts[event_type] += 1
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    event_id = data.get("id")
    class_path = None
    pattern_hint = None
    if isinstance(data, dict):
        features = data.get("features") if isinstance(data.get("features"), dict) else {}
        class_path = features.get("class_path") if isinstance(features, dict) else None
        pattern_hint = features.get("pattern_hint") if isinstance(features, dict) else None
    class_label = "Unknown"
    if class_path:
        class_label = "/".join(class_path)
    if pattern_hint and pattern_hint != "unknown":
        class_label = f"{class_label} ({pattern_hint})"
    if event_id and event_id not in state.unique_ids:
        state.unique_ids.add(event_id)
        state.class_map[event_id] = class_label
        state.class_counts[class_label] += 1
        state.log(f"📡 Event received: {event_id} → {class_label} ✅")
    else:
        state.log(f"📡 Event received: {event_type or 'event'}")


def _render_dashboard(state: MonitorState) -> None:
    uptime = int(time.time() - state.start_time)
    uptime_str = f"{uptime // 3600:02d}:{(uptime % 3600) // 60:02d}:{uptime % 60:02d}"
    total_unique = len(state.unique_ids)

    os.system("clear")
    print(f"{ANSI_BOLD}N-Defender API Monitor{ANSI_RESET}  uptime {uptime_str}")
    print("-")

    status = _status_icon(state.connected)
    ws_status = _status_icon(state.ws_connected)
    health = _status_icon(state.health_ok)
    print(f"System: {status}  API Health: {health}  WS: {ws_status}")

    lat = state.api_metrics.last_latency_ms
    avg = state.api_metrics.avg_latency_ms
    fail = state.api_metrics.fail
    ok = state.api_metrics.ok
    lat_str = f"{lat:.1f} ms" if lat is not None else "-"
    avg_str = f"{avg:.1f} ms" if avg is not None else "-"
    print(f"Latency: {lat_str} (avg {avg_str})  Checks: {ok} ok / {fail} fail")

    last_ts = state.last_event_ts
    last_ts_str = str(last_ts) if last_ts is not None else "-"
    print(f"Last event timestamp: {last_ts_str}")

    print("-")
    print(f"Total unique contacts: {total_unique}")
    print("Counts by classification (unique):")
    if state.class_counts:
        for name, count in state.class_counts.most_common(8):
            print(f"  ✅ {name}: {count}")
    else:
        print("  (no detections yet)")

    print("-")
    print("Event counters:")
    for key in ("RF_CONTACT_NEW", "RF_CONTACT_UPDATE", "RF_CONTACT_LOST"):
        print(f"  {key}: {state.event_counts.get(key, 0)}")

    print("-")
    print("Recent logs:")
    for line in state.logs:
        print(f"  {line}")

    if state.last_error:
        print(_color(f"⚠️  Last error: {state.last_error}", ANSI_YELLOW))


async def run_dashboard(base_url: str, api_key: str | None, log_path: str, interval_s: float) -> None:
    state = MonitorState(base_url=base_url, api_key=api_key)
    state.log("🧪 Test running")

    with open(log_path, "a", encoding="utf-8") as log_file:
        def log_to_file() -> None:
            if not state.logs:
                return
            line = state.logs[-1]
            log_file.write(line + "\n")
            log_file.flush()

        async def poll_logs() -> None:
            last_len = 0
            while True:
                if len(state.logs) != last_len:
                    last_len = len(state.logs)
                    log_to_file()
                await asyncio.sleep(0.2)

        tasks = [
            asyncio.create_task(_poll_health(state, interval_s)),
            asyncio.create_task(_consume_events(state)),
            asyncio.create_task(poll_logs()),
        ]
        try:
            while True:
                _render_dashboard(state)
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass
        finally:
            for task in tasks:
                task.cancel()


def main() -> int:
    parser = argparse.ArgumentParser(prog="api-monitor")
    parser.add_argument("--url", required=True, help="Base API URL (e.g. http://127.0.0.1:8890)")
    parser.add_argument("--api-key", default=os.getenv("API_KEY"), help="API key for X-API-Key header")
    parser.add_argument("--log-file", default="api_monitor.log", help="Log file path")
    parser.add_argument("--interval", type=float, default=2.0, help="Health poll interval seconds")
    parser.add_argument("--self-test", action="store_true", help="Run one-shot API self-test")
    parser.add_argument("--skip-ws", action="store_true", help="Skip WS check in self-test")

    args = parser.parse_args()
    if args.self_test:
        results = asyncio.run(run_self_test(args.url, args.api_key, ws_check=not args.skip_ws))
        for name, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"{status} {name}")
        return 0 if all(results.values()) else 2

    asyncio.run(run_dashboard(args.url, args.api_key, args.log_file, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
