import json

import redis


class RedisEventBus:
    def __init__(self, host: str, port: int = 6379) -> None:
        self._client = redis.Redis(host=host, port=port)

    def publish(self, topic: str, payload: dict) -> None:
        self._client.publish(topic, json.dumps(payload))
