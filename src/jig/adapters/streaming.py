"""流式 SSE 支持 — SOP 管道节点执行结果实时推送。

IDEA-040: 实时流式输出，对标 Reasonix streaming。
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, Generator, List

logger = logging.getLogger(__name__)


class StreamEvent:
    def __init__(self, event: str, data: Any) -> None:
        self.event = event
        self.data = data

    def __str__(self) -> str:
        return f"event: {self.event}\ndata: {json.dumps(self.data)}\n\n"


class StreamManager:
    """SSE 流管理器。"""

    def __init__(self) -> None:
        self._subscribers: List[Any] = []

    def subscribe(self) -> Any:
        queue: List[StreamEvent] = []
        self._subscribers.append(queue)
        return queue

    def publish(self, event: str, data: Any) -> None:
        msg = StreamEvent(event, data)
        for q in self._subscribers:
            q.append(msg)

    def generate(self, queue: List[StreamEvent]) -> Generator[str, None, None]:
        while True:
            while queue:
                yield str(queue.pop(0))
            yield ""
