import logging

from redis_handler.state import State


logger = logging.getLogger(__name__)


def on_join(header, body):
    chat = State.instance.get(header["meetingId"])
    if chat:
        chat.chat_user_id = header["userId"]
        chat.save()
    else:
        logger.debug("Ignoring joining user "+body["name"]+" in meeting "+header["meetingId"])


def on_leave(header, _):
    chat = State.instance.get(header["meetingId"])
    if chat:
        chat.chat_user_id = None
        chat.save()
    else:
        logger.debug("Ignoring leaving user " + header["userId"] + " in meeting " + header["meetingId"])
