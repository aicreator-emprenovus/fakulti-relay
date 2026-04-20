"""Minimal in-process pub/sub for Server-Sent Events (SSE).

Usage:
    from realtime import broker

    # Publisher side (after saving a chat message):
    await broker.publish(session_id, {"type": "message", "message": {...}})

    # Subscriber side (SSE endpoint):
    async for event in broker.subscribe(session_id):
        yield event
"""
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List

logger = logging.getLogger(__name__)


class _Broker:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    async def publish(self, session_id: str, event: dict) -> None:
        queues = list(self._subscribers.get(session_id, []))
        if not queues:
            return
        payload = json.dumps(event, default=str)
        for q in queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for session {session_id}")

    async def subscribe(self, session_id: str) -> AsyncIterator[str]:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(session_id, []).append(q)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=25)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep the connection open through proxies
                    yield ": keep-alive\n\n"
        finally:
            subs = self._subscribers.get(session_id, [])
            if q in subs:
                subs.remove(q)
            if not subs and session_id in self._subscribers:
                del self._subscribers[session_id]


broker = _Broker()
