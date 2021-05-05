import time
from threading import Thread

from django.core.exceptions import MiddlewareNotUsed, AppRegistryNotReady
from django.apps.registry import apps

from redis_handler.connection import RedisHandler
from redis_handler.handlers import on_join, on_leave, on_chat_msg, on_clear_chat, RequestThread
from redis_handler.state import State


class RedisStartupMiddleware:
    def __init__(self, *args, **kwargs):
        redis_handler = RedisHandler()
        RedisHandler.instance = redis_handler
        redis_handler.register("UserJoinedMeetingEvtMsg", on_join)
        redis_handler.register("UserLeftMeetingEvtMsg", on_leave)
        redis_handler.register("GroupChatMessageBroadcastEvtMsg", on_chat_msg)
        redis_handler.register("ClearPublicChatHistoryPubMsg", on_clear_chat)
        redis_handler.start()

        threads = [RequestThread() for i in range(1)]
        for thread in threads:
            thread.start()

        StateLoader().start()
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
