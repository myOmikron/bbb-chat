from django.core.exceptions import MiddlewareNotUsed

from redis_handler.connection import RedisHandler
from redis_handler.handlers import on_join, on_leave, on_chat_msg, on_chat_clear, RequestThread


class RedisStartupMiddleware:
    def __init__(self, *args, **kwargs):
        redis_handler = RedisHandler()
        RedisHandler.instance = redis_handler
        redis_handler.register("UserJoinedMeetingEvtMsg", on_join)
        redis_handler.register("UserLeftMeetingEvtMsg", on_leave)
        redis_handler.register("GroupChatMessageBroadcastEvtMsg", on_chat_msg)
        redis_handler.register("ClearPublicChatHistoryPubMsg", on_chat_clear)
        redis_handler.start()

        threads = [RequestThread() for i in range(1)]
        for thread in threads:
            thread.start()

        raise MiddlewareNotUsed("Good.Design")
