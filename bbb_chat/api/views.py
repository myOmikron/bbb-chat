import json
import hashlib
from datetime import datetime

from django.http import JsonResponse
from django.views.generic import TemplateView

from bbb_chat import settings
from redis_handler.state import State
from redis_handler.connection import RedisHandler
from redis_handler.message_builder import build_message


def validate_request(args, method):
    if "checksum" not in args:
        return {"success": False, "message": "No checksum was given."}
    ret = {"success": False, "message": "Checksum was incorrect."}
    current_timestamp = int(datetime.now().timestamp())
    checksum = args["checksum"]
    del args["checksum"]
    for i in range(0-settings.SHARED_SECRET_TIME_DELTA, settings.SHARED_SECRET_TIME_DELTA):
        tmp_timestamp = current_timestamp - i
        call = method + json.dumps(args)
        if hashlib.sha512((call + settings.SHARED_SECRET + str(tmp_timestamp)).encode("utf-8")).hexdigest() == checksum:
            ret["success"] = True
            ret["message"] = "Checksum is correct"
            break
    return ret


class SendChatMessage(TemplateView):

    def post(self, request, meeting_id="", *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "user_name" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter user_name is mandatory but missing."},
                status=400,
                reason="Parameter user_name is mandatory but missing."
            )
        if "message" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter message is mandatory but missing."},
                status=400,
                reason="Parameter message is mandatory but missing."
            )

        chat = State.instance.get(meeting_id)
        if chat:
            if chat.chat_user_id:
                user = args["user_name"]
                RedisHandler.instance.send(build_message(chat.meeting_id, chat.chat_user_id, chat.chat_user_name,
                                           f'<h4 style="margin-top: 1em; margin-bottom: 0">{user} wrote:</h4>'
                                           + args["message"]))
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


class StartChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "startChatForMeeting")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter meeting_id is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )
        if "chat_user" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter chat_user is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )
        if "callback_uri" not in args:
            if "callback_secret" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_uri is mandatory when specifying callback_secret, but missing."
                    },
                    status=400,
                    reason="Parameter meeting_id is mandatory but missing."
                )

        if "callback_secret" not in args:
            if "callback_uri" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_secret is mandatory when specifying callback_uri, but missing."
                    },
                    status=400,
                    reason="Parameter meeting_id is mandatory but missing."
                )

        if State.instance.get(args["meeting_id"]):
            return JsonResponse(
                {"success": False, "message": "Chat is already registered"},
                status=304,
                reason="Chat is already registered"
            )
        else:
            State.instance.add(
                meeting_id=args["meeting_id"],
                chat_user=args["chat_user"],
                callback_uri="" if "callback_uri" not in args else args["callback_uri"],
                callback_secret="" if "callback_secret" not in args else args["callback_secret"],
            )
            return JsonResponse({"success": True, "message": "Chat registered successfully"})


class EndChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        try:
            args = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "Decoding data failed"},
                status=400,
                reason="Decoding data failed"
            )
        validated = validate_request(args, "endChatForMeeting")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter meeting_id is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )

        if State.instance.get(args["meeting_id"]):
            State.instance.remove(args["meeting_id"])
            return JsonResponse({"success": True, "message": "Chat was successfully ended"})
        else:
            return JsonResponse({"success": False, "message": "Chat was not found"}, status=404,
                                reason="Chat was not found")
