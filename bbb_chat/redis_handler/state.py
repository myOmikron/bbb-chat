from api.models import Chat


class State:
    """
    A cache for the Chat model, to decrease db load
    """

    instance = None

    def __init__(self):
        self.chats = {}
        for chat in Chat.objects.all():
            self.chats[chat.meeting_id] = chat

    def add(self, meeting_id, chat_user, callback_uri="", callback_secret="", callback_id=""):
        if meeting_id in self.chats:
            raise ValueError("Chat already exists")

        chat = Chat.objects.create(meeting_id=meeting_id,
                                   chat_user_name=chat_user,
                                   callback_uri=callback_uri,
                                   callback_secret=callback_secret,
                                   callback_id=callback_id)
        self.chats[meeting_id] = chat

    def remove(self, meeting_id):
        self.chats[meeting_id].delete()
        del self.chats[meeting_id]

    def get(self, meeting_id):
        try:
            return self.chats[meeting_id]
        except KeyError:
            return None
