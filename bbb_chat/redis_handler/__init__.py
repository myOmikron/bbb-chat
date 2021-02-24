import time
from threading import Thread

from django.core.exceptions import MiddlewareNotUsed, AppRegistryNotReady
from django.apps.registry import apps

from redis_handler.redis import startup, register_handler
from redis_handler.join_leave import on_join, on_leave
from redis_handler.chat_message import on_chat_msg, Worker
from redis_handler.state import State


class RedisStartupMiddleware:
    def __init__(self, *args, **kwargs):
        register_handler("UserJoinedMeetingEvtMsg", on_join)
        register_handler("UserLeftMeetingEvtMsg", on_leave)
        register_handler("GroupChatMessageBroadcastEvtMsg", on_chat_msg)
        workers = [Worker() for i in range(1)]
        StateLoader().start()
        startup()
        raise MiddlewareNotUsed("Good.Design")


class StateLoader(Thread):
    def run(self):
        while True:
            try:
                apps.check_models_ready()
                State.instance = State()
                break
            except AppRegistryNotReady:
                time.sleep(1)
