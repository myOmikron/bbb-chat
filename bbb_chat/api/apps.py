import logging

from django.apps import AppConfig
from django.db import OperationalError
from django.db.models.signals import post_save, pre_delete

from redis_sync.connection import RedisHandler
from redis_sync.model_signals import ModelSignalHandler


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        from api.models import Chat

        try:
            for chat in Chat.objects.all():
                Chat.objects.internal[chat.internal_meeting_id] = chat
                Chat.objects.external[chat.external_meeting_id] = chat
        except OperationalError:
            logging.exception("Missing migrations?")

        Chat.objects.register_signals()

        rh = RedisHandler()
        msh = ModelSignalHandler(rh)
        msh.register(Chat, [post_save, pre_delete])
        rh.start()
