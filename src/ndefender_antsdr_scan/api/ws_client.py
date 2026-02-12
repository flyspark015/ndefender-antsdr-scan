from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class WsClientConfig:
    url: str
    connect_timeout_s: float = 5.0


class WsClient:
    def __init__(self, config: WsClientConfig) -> None:
        self._config = config

    def connect(self) -> None:
        raise NotImplementedError("WebSocket client not implemented yet")

    def send_event(self, event: dict) -> None:
        raise NotImplementedError("WebSocket client not implemented yet")

    def send_many(self, events: Iterable[dict]) -> None:
        for event in events:
            self.send_event(event)

    def close(self) -> None:
        return None


class NullWsClient(WsClient):
    def __init__(self) -> None:
        super().__init__(WsClientConfig(url=""))

    def connect(self) -> None:
        return None

    def send_event(self, event: dict) -> None:
        return None

    def close(self) -> None:
        return None
