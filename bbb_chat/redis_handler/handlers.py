import logging
import os
from queue import Queue
import json
import hashlib
from datetime import datetime
from threading import Thread

import requests

from redis_handler.state import State


logger = logging.getLogger(__name__)


def on_join(header, body):
    chat = State.instance.get(header["meetingId"])
    if chat:
        chat.chat_user_id = header["userId"]
        chat.save()
    else:
        logger.debug("Ignoring joining user "+body["name"]+" in meeting "+header["meetingId"])


def on_leave(header, _):
    chat = State.instance.get(header["meetingId"])
    if chat:
        chat.chat_user_id = None
        chat.save()
    else:
        logger.debug("Ignoring leaving user " + header["userId"] + " in meeting " + header["meetingId"])


def on_chat_msg(header, body):
    if body["chatId"] != "MAIN-PUBLIC-GROUP-CHAT":
        return

    chat = State.instance.get(header["meetingId"])
    if not chat:
        return

    if not chat.callback_uri or not chat.callback_secret:
        return

    params = {
        "meeting_id": header["meetingId"],
        "user_name": body["msg"]["sender"]["name"],
        "message": body["msg"]["message"]
    }

    params["checksum"] = hashlib.sha512((
        os.path.basename(chat.callback_uri.rstrip("/"))
        + json.dumps(params)
        + chat.callback_secret
        + str(int(datetime.now().timestamp()))
    ).encode("utf-8")).hexdigest()

    RequestThread.queue.put((chat.callback_uri, json.dumps(params)))


class RequestThread(Thread):

    queue = Queue()

    def run(self):
        self.running = True
        while self.running:
            uri, data = self.queue.get()
            requests.post(uri, data=data)

    def stop(self):
        self.running = False
