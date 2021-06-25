import logging
from typing import Type

from django.db.models import Model
from django.db.models.signals import post_delete, pre_delete, post_save, pre_save, post_init, pre_init
from django.apps import apps
from django.dispatch import Signal

from .connection import RedisHandler


logger = logging.getLogger(__name__)


_signals2names = {
    pre_init: "pre_init",
    post_init: "post_init",
    pre_save: "pre_save",
    post_save: "post_save",
    pre_delete: "pre_delete",
    post_delete: "post_delete",
}
_names2signals = dict((v, k) for k, v in _signals2names.items())


class ModelSignalHandler:

    def __init__(self, redis_handler: RedisHandler):
        self.redis_handler = redis_handler
        redis_handler.handlers["model-signals"] = self._receive

    def register(self, model: Type[Model], signals=None):
        if signals is None:
            signals = list(_signals2names.keys())

        for signal in signals:
            signal.connect(
                receiver=self._send,
                sender=model,
                dispatch_uid=f"msh-{_signals2names[signal]}-{model._meta.model_name}",
                weak=False
            )

    def _send(self, signal=None, sender=None, instance=None, from_redis=False, **named):
        if signal not in _signals2names:
            raise NotImplemented("Got unknown signal")

        if from_redis:
            return

        self.redis_handler.send(
            "model-signals",
            {
                "signal": _signals2names[signal],
                "model_name": sender._meta.model_name,
                "app_label": sender._meta.app_label,
                "named": {"from_redis": True, **named},
                "instance": dict(
                    (k, v) for k, v in instance.__dict__.items() if not k.startswith("_")) if instance else None
            }
        )

    def _receive(self, data: dict):
        model: Type[Model] = apps.get_model(data["app_label"], data["model_name"])
        instance: Model = model(**data["instance"])
        signal: Signal = _names2signals[data["signal"]]
        signal.send(model, instance=instance, **data["named"])
