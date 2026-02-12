import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from ndefender_antsdr_scan.api.bus import EventBus
from ndefender_antsdr_scan.api.runtime import ReplayResult
from ndefender_antsdr_scan.api.server import ApiState, create_app
from ndefender_antsdr_scan.core.config import ApiConfig, load_config

import tools.api_monitor as api_monitor


class _DummyRunner:
    def __init__(self) -> None:
        self.is_running = False
        self.ws_connected = False
        self.stats = type("Stats", (), {"frames_processed": 1, "detections_processed": 2, "events_emitted": 3})()

    def start(self) -> bool:
        return True

    def stop(self) -> bool:
        return True

    def replay(self, log_path: str, output_path: str | None = None, max_events: int | None = None) -> ReplayResult:
        return ReplayResult(frames=1, detections=2, events_emitted=3)


class ApiMonitorTests(unittest.IsolatedAsyncioTestCase):
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
        app = create_app(state)
        self.server = TestServer(app)
        self.client = TestClient(self.server)
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()

    async def test_self_test(self) -> None:
        base_url = str(self.client.make_url("/")).rstrip("/")
        results = await api_monitor.run_self_test(base_url, api_key=None, ws_check=False)
        self.assertTrue(results["health"])
        self.assertTrue(results["stats"])
        self.assertTrue(results["config"])
        self.assertTrue(results["events_last"])


if __name__ == "__main__":
    unittest.main()
