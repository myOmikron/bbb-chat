from django.core.exceptions import MiddlewareNotUsed

from redis_handler.redis import startup, register_handler
from redis_handler.join_leave import on_join, on_leave


class RedisStartupMiddleware:
    def __init__(self, *args, **kwargs):
        register_handler("UserJoinedMeetingEvtMsg", on_join)
        register_handler("UserLeftMeetingEvtMsg", on_leave)
        startup()
        raise MiddlewareNotUsed("Good.Design")
