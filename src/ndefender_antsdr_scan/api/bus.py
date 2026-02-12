from __future__ import annotations

import asyncio
import threading
from collections import deque
from typing import Deque


def _safe_put(queue: asyncio.Queue, event: dict) -> None:
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            return


class EventBus:
    def __init__(self, maxlen: int = 500) -> None:
        self._buffer: Deque[dict] = deque(maxlen=maxlen)
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def publish(self, event: dict) -> None:
        with self._lock:
            self._buffer.append(event)
            subscribers = list(self._subscribers)
        loop = self._loop
        if loop is not None and loop.is_running():
            for queue in subscribers:
                loop.call_soon_threadsafe(_safe_put, queue, event)
            return
        for queue in subscribers:
            _safe_put(queue, event)

    def last(self, limit: int = 50) -> list[dict]:
        with self._lock:
            if limit <= 0:
                return []
            return list(self._buffer)[-limit:]

    def subscribe(self, max_queue: int = 100) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.discard(queue)
