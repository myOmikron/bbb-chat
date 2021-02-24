import json

from django.views.generic import TemplateView


def validate_request(args):
    if "checksum" not in args:
        pass
    print(args)


class SendChatMessage(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        validate_request(args)
        if "meeting_id" not in args:
            pass
        if "user_name" not in args:
            pass
        if "message" not in args:
            pass


class StartChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        if "meeting_id" not in args:
            pass
        if "user_name" not in args:
            pass
        if "enable_callbacks" not in args:
            pass
        if "callback_uri" not in args:
            pass


class EndChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        if "meeting_id" not in args:
            pass
