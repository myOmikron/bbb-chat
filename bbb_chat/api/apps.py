import logging

from django.apps import AppConfig
from django.db import OperationalError


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
