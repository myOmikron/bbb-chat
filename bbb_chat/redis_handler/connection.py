import json
import logging

import redis


logger = logging.getLogger(__name__)


class RedisHandler:

    instance = None

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.connection = redis.Redis(host=host, port=port, db=db)
        self.pubsub = self.connection.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(**{"from-akka-apps-redis-channel": self._receive})
        self.thread = None
        self.handlers = {}

    def start(self):
        self.thread = self.pubsub.run_in_thread(sleep_time=0.001)

    def send(self, message: dict):
        self.connection.publish("to-akka-apps-redis-channel", json.dumps(message))

    def register(self, event: str, func):
        self.handlers[event] = func

    def _receive(self, obj):
        message: dict = json.loads(obj["data"].decode())
        try:
            header = message["core"]["header"]
            body = message["core"]["body"]
            logger.debug("Received redis message:\n"
                         "header: " + str(header) + "\n"
                         "body: " + str(body) + "\n")
            assert header["name"]
        except KeyError:
            logger.error("Malformed redis message: "+str(message))
            return

        if header["name"] in self.handlers:
            try:
                self.handlers[header["name"]](header, body)
            except Exception:
                logger.exception("An exception occurred in the redis handler: "+header["name"])
        else:
            logger.debug("Event '"+str(header["name"])+"' has no handler")

