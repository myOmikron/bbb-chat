import json
import logging

import redis


logger = logging.getLogger(__name__)

CONNECTION = None
PUBSUB = None
THREAD = None
HANDLERS = {}


def register_handler(event, func):
    global HANDLERS
    HANDLERS[event] = func


def _receive(obj):
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

    if header["name"] in HANDLERS:
        try:
            HANDLERS[header["name"]](header, body)
        except Exception:
            logger.exception("An exception occurred in the redis handler: "+header["name"])
    else:
        logger.debug("Event '"+str(header["name"])+"' has no handler")


def send(message: dict):
    global CONNECTION
    CONNECTION.publish("to-akka-apps-redis-channel", json.dumps(message))


def startup(host="localhost", port=6379, db=0):
    global CONNECTION, PUBSUB, THREAD
    CONNECTION = redis.Redis(host=host, port=port, db=db)
    PUBSUB = CONNECTION.pubsub(ignore_subscribe_messages=True)
    PUBSUB.subscribe(**{"from-akka-apps-redis-channel": _receive})
    THREAD = PUBSUB.run_in_thread(sleep_time=0.001)
