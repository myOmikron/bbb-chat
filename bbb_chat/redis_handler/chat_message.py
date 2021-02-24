import logging
from queue import Queue
import json
import hashlib
from datetime import datetime
from threading import Thread

import requests

from api.models import Chat


logger = logging.getLogger(__name__)
queue = Queue()


def on_chat_msg(header, body):
    if body["chatId"] != "MAIN-PUBLIC-GROUP-CHAT":
        return

    try:
        chat = Chat.objects.get(meeting_id=header["meetingId"])
    except Chat.DoesNotExist:
        return

    if not chat.callback_uri or not chat.callback_secret:
        return

    params = {
        "meeting_id": header["meetingId"],
        "user_name": body["msg"]["sender"]["name"],
        "message": body["msg"]["message"]
    }

    call = chat.callback_uri + json.dumps(params)

    params["checksum"] = hashlib.sha512(
        (call + chat.callback_secret + str(int(datetime.now().timestamp()))).encode("utf-8")
    ).hexdigest()

    queue.put((chat.callback_uri, json.dumps(params)))


class Worker(Thread):

    running: bool

    def run(self):
        self.running = True
        while self.running:
            uri, data = queue.get()
            requests.post(uri, data=data)

    def stop(self):
        self.running = False
