import json
import logging

import redis


logger = logging.getLogger(__name__)


class RedisHandler:

    channel = "redis-sync"

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.connection = redis.Redis(host=host, port=port, db=db)
        self.pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{self.channel: self._receive})
        self.handlers = {}
        self.thread = None

    def start(self):
        self.thread = self.pubsub.run_in_thread(sleep_time=0.001)

    def _send(self, message: dict):
        logger.debug(f"Sending: {message}")
        self.connection.publish(self.channel, json.dumps(message))

    def send(self, msg_type: str, msg_data):
        self._send({"type": msg_type, "data": msg_data})

    def _receive(self, obj):
        message: dict = json.loads(obj["data"].decode())
        logger.debug(f"Received: {message}")
        msg_type: str = message["type"]
        msg_data = message["data"]

        if msg_type in self.handlers:
            self.handlers[msg_type](msg_data)
        else:
            logger.debug(f"Unknown message type: '{message['type']}'")
