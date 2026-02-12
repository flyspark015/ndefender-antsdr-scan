from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from ndefender_antsdr_scan.io.jsonl import write_jsonl
from ndefender_antsdr_scan.api.ws_client import NullWsClient, WsClient

DEFAULT_LOG_PATH = "/opt/ndefender/logs/antsdr_scan.jsonl"


@dataclass
class EmitConfig:
    jsonl_path: str = DEFAULT_LOG_PATH


class EventEmitter:
    def __init__(self, config: EmitConfig | None = None, ws_client: WsClient | None = None) -> None:
        self._config = config or EmitConfig()
        self._ws_client = ws_client or NullWsClient()
        self._ensure_log_dir()

    def emit(self, event: dict) -> None:
        write_jsonl(self._config.jsonl_path, [event])
        self._ws_client.send_event(event)

    def emit_many(self, events: Iterable[dict]) -> None:
        events_list = list(events)
        if not events_list:
            return
        write_jsonl(self._config.jsonl_path, events_list)
        self._ws_client.send_many(events_list)

    def _ensure_log_dir(self) -> None:
        log_dir = os.path.dirname(self._config.jsonl_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
