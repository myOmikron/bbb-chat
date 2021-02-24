from django.db import models


class Chat(models.Model):
    meeting_id = models.CharField(max_length=255, default="")
    user_name = models.CharField(max_length=255, default="")
    user_id = models.CharField(max_length=255, blank=True, null=True)
    callback_uri = models.CharField(max_length=255, default="")
    callback_secret = models.CharField(max_length=255, default="")

    class Meta:
        unique_together = ("meeting_id", "user_name")
