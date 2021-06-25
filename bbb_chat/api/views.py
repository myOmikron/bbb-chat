from bigbluebutton_api_python import BigBlueButton
from django.http import JsonResponse
from django.views import View

from bbb_chat import settings
from bbb_common_api.views import PostApiPoint
from redis_handler.connection import RedisHandler
from redis_handler.message_builder import build_message
from api.models import Chat


bbb = BigBlueButton(settings.BBB_URL, settings.BBB_SECRET)


class RunningChats(View):

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "count": Chat.objects.count(),
            "chat_ids": [chat.external_meeting_id for chat in Chat.objects.all()]
        })


class SendMessage(PostApiPoint):

    endpoint = "sendMessage"
    required_parameters = ["chat_id", "message", "user_name"]

    def safe_post(self, request, parameters, *args, **kwargs):
        chat = Chat.objects.get(parameters["chat_id"])
        if chat:
            if chat.chat_user_id:
                RedisHandler.instance.send(build_message(
                    chat.internal_meeting_id, chat.chat_user_id, chat.chat_user_name,
                    settings.MESSAGE_TEMPLATE.format(user=parameters["user_name"], message=parameters["message"])
                ))
                return JsonResponse(
                    {"success": True, "message": "Message sent successfully"}
                )
            else:
                return JsonResponse(
                    {"success": False, "message": "The chat user hasn't joined the meeting yet."},
                    status=404
                )
        else:
            return JsonResponse(
                {"success": False, "message": "This meeting's chat wasn't started."},
                status=404
            )


class StartChat(PostApiPoint):

    endpoint = "startChat"
    required_parameters = ["chat_id", "chat_user"]

    def safe_post(self, request, parameters, *args, **kwargs):
        callback_params = ["callback_uri", "callback_secret", "callback_id"]
        missing = []
        for param in callback_params:
            if param not in parameters:
                missing.append(param)

        if len(missing) == 1:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Parameter {missing[0]} is mandatory when enabling callbacks, but is missing"
                },
                status=403,
                reason=f"Parameter {missing[0]} is mandatory when enabling callbacks, but is missing"
            )
        elif len(missing) == 2:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Parameters {missing[0]} and {missing[1]} "
                               f"are mandatory when enabling callbacks, but are missing"
                },
                status=403,
                reason=f"Parameters {missing[0]} and {missing[1]} "
                       f"are mandatory when enabling callbacks, but are missing"
            )

        if Chat.objects.get(parameters["chat_id"]):
            return JsonResponse(
                {"success": False, "message": "Chat is already registered"},
                status=304,
                reason="Chat is already registered"
            )
        else:
            internal_meeting_id = bbb.get_meeting_info(parameters["chat_id"]).get_meetinginfo().get_internal_meetingid()
            if len(missing) == 0:
                Chat.objects.create(
                    external_meeting_id=parameters["chat_id"],
                    internal_meeting_id=internal_meeting_id,
                    chat_user=parameters["chat_user"],
                    callback_uri=parameters["callback_uri"],
                    callback_secret=parameters["callback_secret"],
                    callback_id=parameters["callback_id"],
                )
            else:
                Chat.objects.create(
                    external_meeting_id=parameters["chat_id"],
                    internal_meeting_id=internal_meeting_id,
                    chat_user=parameters["chat_user"]
                )
            return JsonResponse({"success": True, "message": "Chat registered successfully"})


class EndChat(PostApiPoint):

    endpoint = "endChat"
    required_parameters = ["chat_id"]

    def safe_post(self, request, parameters, *args, **kwargs):
        chat = Chat.objects.get(parameters["chat_id"])
        if chat:
            chat.delete()
            return JsonResponse({"success": True, "message": "Chat was successfully ended"})
        else:
            return JsonResponse({"success": False, "message": "Chat was not found"}, status=404,
                                reason="Chat was not found")
