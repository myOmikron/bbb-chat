from django.db import models

from redis_handler.connection import send as redis_send
from redis_handler.message_builder import build_message


class Chat(models.Model):
    meeting_id = models.CharField(max_length=255, default="", unique=True)
    chat_user_name = models.CharField(max_length=255, default="")
    chat_user_id = models.CharField(max_length=255, blank=True, null=True)
    callback_uri = models.CharField(max_length=255, default="")
    callback_secret = models.CharField(max_length=255, default="")

    def send(self, message):
        return redis_send(build_message(self.meeting_id, self.chat_user_id, self.chat_user_name, message))
