from django.db import models
from django.db.models.signals import post_save, pre_delete


class CachedChatManager(models.Manager):

    def __init__(self):
        super().__init__()
        self.internal = {}
        """Mapping from internal meeting id to chat object"""

        self.external = {}
        """Mapping from external meeting id to chat object"""

        # Cache will be populated in apps.py

    def get(self, value=None, **kwargs):
        if value is None:
            return super().get(**kwargs)
        elif value in self.internal:
            return self.internal[value]
        elif value in self.external:
            return self.external[value]
        else:
            return None

    def on_object_save(self, instance: "Chat", **kwargs):
        self.internal[instance.internal_meeting_id] = instance
        self.external[instance.external_meeting_id] = instance

    def on_object_delete(self, instance: "Chat", **kwargs):
        self.internal[instance.internal_meeting_id] = None
        self.external[instance.external_meeting_id] = None

    def register_signals(self):
        post_save.connect(self.on_object_save, sender=self.model, dispatch_uid="on_chat_save")
        pre_delete.connect(self.on_object_delete, sender=self.model, dispatch_uid="on_chat_delete")


class Chat(models.Model):
    external_meeting_id = models.CharField(max_length=255, default="", unique=True)
    internal_meeting_id = models.CharField(max_length=255, default="", unique=True)
    chat_user_name = models.CharField(max_length=255, default="")
    chat_user_id = models.CharField(max_length=255, blank=True, null=True)
    callback_uri = models.CharField(max_length=255, default="")
    callback_secret = models.CharField(max_length=255, default="")
    callback_id = models.CharField(max_length=255, default="")

    objects = CachedChatManager()
