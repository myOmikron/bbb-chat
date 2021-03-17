import json

from django.http import JsonResponse
from django.views.generic import TemplateView
from rc_protocol import validate_checksum

from bbb_chat import settings
from redis_handler.state import State
from redis_handler.connection import RedisHandler
from redis_handler.message_builder import build_message
from api.models import Chat


class _PostApiPoint(TemplateView):

    required_parameters: list
    endpoint: str

    def post(self, request, *args, **kwargs):
        # Decode json
        try:
            parameters = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )

        # Validate checksum
        try:
            if not validate_checksum(parameters, settings.SHARED_SECRET,
                                     self.endpoint, settings.SHARED_SECRET_TIME_DELTA):
                return JsonResponse(
                    {"success": False, "message": "Checksum was incorrect."},
                    status=400,
                    reason="Checksum was incorrect."
                )
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "No checksum was given."},
                status=400,
                reason="No checksum was given."
            )

        # Check required parameters
        for param in self.required_parameters:
            if param not in parameters:
                return JsonResponse(
                    {"success": False, "message": f"Parameter {param} is mandatory but missing."},
                    status=400,
                    reason=f"Parameter {param} is mandatory but missing."
                )

        # Hand over to subclass
        return self._post(request, parameters, *args, **kwargs)

    def _post(self, request, parameters, *args, **kwargs):
        return NotImplemented


class RunningChats(TemplateView):

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            "count": Chat.objects.count(),
            "chat_ids": [chat.external_meeting_id for chat in Chat.objects.all()]
        })


class SendMessage(_PostApiPoint):

    endpoint = "sendMessage"
    required_parameters = ["chat_id", "message", "user_name"]

    def _post(self, request, parameters, *args, **kwargs):
        chat = State.instance.get(parameters["chat_id"])
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


class StartChat(_PostApiPoint):

    endpoint = "startChat"
    required_parameters = ["chat_id", "chat_user"]

    def _post(self, request, parameters, *args, **kwargs):
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

        if State.instance.get(parameters["chat_id"]):
            return JsonResponse(
                {"success": False, "message": "Chat is already registered"},
                status=304,
                reason="Chat is already registered"
            )
        else:
            if len(missing) == 0:
                State.instance.add(
                    meeting_id=parameters["chat_id"],
                    chat_user=parameters["chat_user"],
                    callback_uri=parameters["callback_uri"],
                    callback_secret=parameters["callback_secret"],
                    callback_id=parameters["callback_id"],
                )
            else:
                State.instance.add(
                    meeting_id=parameters["chat_id"],
                    chat_user=parameters["chat_user"]
                )
            return JsonResponse({"success": True, "message": "Chat registered successfully"})


class EndChat(_PostApiPoint):

    endpoint = "endChat"
    required_parameters = ["chat_id"]

    def _post(self, request, parameters, *args, **kwargs):
        if State.instance.get(parameters["chat_id"]):
            State.instance.remove(parameters["chat_id"])
            return JsonResponse({"success": True, "message": "Chat was successfully ended"})
        else:
            return JsonResponse({"success": False, "message": "Chat was not found"}, status=404,
                                reason="Chat was not found")
