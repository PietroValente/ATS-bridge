from typing import Protocol


class EventBus(Protocol):
    def publish(self, topic: str, payload: dict) -> None: ...
