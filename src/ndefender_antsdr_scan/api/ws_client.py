from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class WsClientConfig:
    url: str
    connect_timeout_s: float = 5.0
    send_timeout_s: float = 2.0
    max_retries: int = 3
    retry_backoff_s: float = 1.0
    enabled: bool = False


class WsClient:
    def __init__(self, config: WsClientConfig) -> None:
        self._config = config
        self._ws: Optional["websocket.WebSocket"] = None

    def connect(self) -> None:
        if not self._config.url:
            raise ValueError("WebSocket url is required")
        self._connect_with_retries()

    def send_event(self, event: dict) -> None:
        payload = json.dumps(event, separators=(",", ":"), ensure_ascii=True)
        self._send_with_retries(payload)

    def send_many(self, events: Iterable[dict]) -> None:
        for event in events:
            self.send_event(event)

    def close(self) -> None:
        if self._ws is None:
            return None
        try:
            self._ws.close()
        finally:
            self._ws = None

    def _connect_with_retries(self) -> None:
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                self._connect_once()
                return
            except Exception as exc:
                last_error = exc
                time.sleep(self._config.retry_backoff_s * (attempt + 1))
        if last_error is not None:
            raise last_error

    def _connect_once(self) -> None:
        import websocket  # type: ignore

        ws = websocket.WebSocket()
        ws.settimeout(self._config.connect_timeout_s)
        ws.connect(self._config.url)
        self._ws = ws

    def _send_with_retries(self, payload: str) -> None:
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                if self._ws is None:
                    self._connect_once()
                assert self._ws is not None
                self._ws.send(payload)
                return
            except Exception as exc:
                last_error = exc
                self.close()
                time.sleep(self._config.retry_backoff_s * (attempt + 1))
        if last_error is not None:
            raise last_error


class NullWsClient(WsClient):
    def __init__(self) -> None:
        super().__init__(WsClientConfig(url="", enabled=False))

    def connect(self) -> None:
        return None

    def send_event(self, event: dict) -> None:
        return None

    def close(self) -> None:
        return None
