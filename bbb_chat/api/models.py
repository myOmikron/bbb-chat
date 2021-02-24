from django.db import models


class Chat(models.Model):
    meeting_id = models.CharField(max_length=255, default="", unique=True)
    chat_user_name = models.CharField(max_length=255, default="")
    chat_user_id = models.CharField(max_length=255, blank=True, null=True)
    callback_uri = models.CharField(max_length=255, default="")
    callback_secret = models.CharField(max_length=255, default="")
