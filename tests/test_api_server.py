import unittest
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ndefender_antsdr_scan.api.bus import EventBus
from ndefender_antsdr_scan.api.runtime import ReplayResult
from ndefender_antsdr_scan.api.server import ApiState, create_app
from ndefender_antsdr_scan.core.config import ApiConfig, load_config


class _DummyRunner:
    def __init__(self) -> None:
        self.is_running = False
        self.stats = type("Stats", (), {"frames_processed": 1, "detections_processed": 2, "events_emitted": 3})()
        self.ws_connected = False

    def start(self) -> bool:
        if self.is_running:
            return False
        self.is_running = True
        return True

    def stop(self) -> bool:
        if not self.is_running:
            return False
        self.is_running = False
        return True

    def replay(self, log_path: str, output_path: str | None = None, max_events: int | None = None) -> ReplayResult:
        return ReplayResult(frames=1, detections=2, events_emitted=3)


class ApiServerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        config = load_config("config/default.yaml")
        api_config = ApiConfig(enabled=True, bind="127.0.0.1", port=0, api_key=None, max_clients=10, event_buffer=10)
        event_bus = EventBus(maxlen=10)
        runner = _DummyRunner()
        state = ApiState(
            config_path=Path("config/default.yaml"),
            config=config,
            api_config=api_config,
            runner=runner,
            event_bus=event_bus,
        )
        self.app = create_app(state)
        self.server = TestServer(self.app)
        self.client = TestClient(self.server)
        await self.client.start_server()
        self.event_bus = event_bus

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_health(self) -> None:
        resp = await self.client.get("/api/v1/health")
        self.assertEqual(resp.status, 200)
        payload = await resp.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("last_event_timestamp_ms", payload)

    async def test_stats(self) -> None:
        resp = await self.client.get("/api/v1/stats")
        self.assertEqual(resp.status, 200)
        payload = await resp.json()
        self.assertEqual(payload["events_emitted"], 3)

    async def test_events_last(self) -> None:
        self.event_bus.publish({"type": "RF_CONTACT_NEW"})
        resp = await self.client.get("/api/v1/events/last?limit=1")
        self.assertEqual(resp.status, 200)
        payload = await resp.json()
        self.assertEqual(len(payload["events"]), 1)

    async def test_run_start_stop(self) -> None:
        resp = await self.client.post("/api/v1/run/start")
        self.assertEqual(resp.status, 200)
        resp = await self.client.post("/api/v1/run/stop")
        self.assertEqual(resp.status, 200)

    async def test_replay_missing_log_path(self) -> None:
        resp = await self.client.post("/api/v1/run/replay", json={})
        self.assertEqual(resp.status, 400)
        payload = await resp.json()
        self.assertEqual(payload["error"]["code"], "bad_request")

    async def test_replay_missing_file(self) -> None:
        resp = await self.client.post(
            "/api/v1/run/replay",
            json={"log_path": "/tmp/does-not-exist.jsonl"},
        )
        self.assertEqual(resp.status, 404)
        payload = await resp.json()
        self.assertEqual(payload["error"]["code"], "not_found")

    async def test_config_redacts_api_key(self) -> None:
        resp = await self.client.get("/api/v1/config")
        self.assertEqual(resp.status, 200)
        payload = await resp.json()
        self.assertEqual(payload["api"]["api_key"], "")


class ApiServerAuthTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        config = load_config("config/default.yaml")
        api_config = ApiConfig(enabled=True, bind="127.0.0.1", port=0, api_key="secret", max_clients=10, event_buffer=10)
        event_bus = EventBus(maxlen=10)
        runner = _DummyRunner()
        state = ApiState(
            config_path=Path("config/default.yaml"),
            config=config,
            api_config=api_config,
            runner=runner,
            event_bus=event_bus,
        )
        self.app = create_app(state)
        self.server = TestServer(self.app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_auth_required(self) -> None:
        resp = await self.client.get("/api/v1/health")
        self.assertEqual(resp.status, 401)

    async def test_auth_success(self) -> None:
        resp = await self.client.get("/api/v1/health", headers={"X-API-Key": "secret"})
        self.assertEqual(resp.status, 200)


if __name__ == "__main__":
    unittest.main()
