from django.conf import settings

from api.models import Chat

from bigbluebutton_api_python import BigBlueButton


bbb_api = BigBlueButton(settings.BBB_URL, settings.BBB_SECRET)


class State:
    """
    A cache for the Chat model, to decrease db load
    """

    instance = None

    def __init__(self):
        self.internal = {}
        """Mapping from internal meeting id to chat object"""

        self.external = {}
        """Mapping from external meeting id to chat object"""

        for chat in Chat.objects.all():
            self._add(chat)

    def _add(self, chat):
        self.external[chat.external_meeting_id] = chat
        self.internal[chat.internal_meeting_id] = chat

    def add(self, meeting_id, chat_user, callback_uri="", callback_secret="", callback_id=""):
        """
        :param meeting_id: the external meeting id
        :param chat_user: name of the user who should act as chat bridge
        :param callback_uri:
        :param callback_secret:
        :param callback_id:
        """
        if meeting_id in self.external:
            raise ValueError("Chat already exists")

        self._add(Chat.objects.create(
            external_meeting_id=meeting_id,
            internal_meeting_id=str(bbb_api.get_meeting_info(meeting_id)["xml"]["internalMeetingID"]),
            chat_user_name=chat_user,
            callback_uri=callback_uri,
            callback_secret=callback_secret,
            callback_id=callback_id
        ))

    def remove(self, meeting_id):
        """
        :param meeting_id: the external meeting id
        """
        chat = self.external[meeting_id]
        del self.external[chat.external_meeting_id]
        del self.internal[chat.internal_meeting_id]
        chat.delete()

    def get(self, meeting_id):
        """
        :param meeting_id: the external or internal meeting id
        """
        if meeting_id in self.internal:
            return self.internal[meeting_id]
        elif meeting_id in self.external:
            return self.external[meeting_id]
        else:
            return None
