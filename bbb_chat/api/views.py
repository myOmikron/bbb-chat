import json
import hashlib
from datetime import datetime

from django.http import JsonResponse
from django.views.generic import TemplateView

from bbb_chat import settings
from redis_handler.connection import send
from redis_handler.message_builder import build_message
from redis_handler.state import State


def validate_request(args, method):
    if "checksum" not in args:
        return {"success": False, "message": "No checksum was given."}
    ret = {"success": False, "message": "Checksum was incorrect."}
    current_timestamp = int(datetime.now().timestamp())
    for i in range(settings.SHARED_SECRET_TIME_DELTA):
        tmp_timestamp = current_timestamp - i
        call = method + json.dumps(args)
        if hashlib.sha512((call + settings.SHARED_SECRET + str(tmp_timestamp)).encode("utf-8")).hexdigest() == args["checksum"]:
            ret["success"] = True
            ret["message"] = "Checksum is correct"
            break
    return ret


class SendChatMessage(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.loads(request.body)
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter meeting_id is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )
        if "user_name" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter user_name is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )
        if "message" not in args:
            return JsonResponse(
                {"success": False, "message": "Parameter message is mandatory but missing."},
                status=400,
                reason="Parameter meeting_id is mandatory but missing."
            )

        send(build_message(args["meeting_id"], args["user_name"], args["message"]))


class StartChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.loads(request.body)
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
            return JsonResponse({"success": False, "message": "Chat is already registered"}, status=304)
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
        args = json.loads(request.body)
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
