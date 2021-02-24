import logging

from api.models import Chat


logger = logging.getLogger(__name__)


def on_join(header, body):
    try:
        chat = Chat.objects.get(
            meeting_id=header["meetingId"],
            user_name=body["name"]
        )
        chat.user_id = header["userId"]
        chat.save()
    except Chat.DoesNotExist:
        logger.debug("Ignoring joining user "+body["name"]+" in meeting "+header["meetingId"])


def on_leave(header, _):
    try:
        chat = Chat.objects.get(
            meeting_id=header["meetingId"],
            user_id=header["userId"]
        )
        chat.user_id = None
        chat.save()
    except Chat.DoesNotExist:
        logger.debug("Ignoring leaving user "+header["userId"]+" in meeting "+header["meetingId"])

