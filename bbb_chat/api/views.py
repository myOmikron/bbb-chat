import json
import hashlib
from datetime import datetime

from django.http import JsonResponse
from django.views.generic import TemplateView

from api.models import Chat
from bbb_chat import settings
from redis_handler.redis import send
from redis_handler.message_builder import build_message


def validate_request(args, method):
    if "checksum" not in args:
        return {"success": False, "message": "No checksum was given."}
    ret = {"success": False, "message": "Checksum was incorrect."}
    current_timestamp = int(datetime.now().timestamp())
    for i in range(settings.SHARED_SECRET_TIME_DELTA):
        tmp_timestamp = current_timestamp - i
        call = method + json.dumps(args)
        if hashlib.sha512(call + settings.SHARED_SECRET + str(tmp_timestamp)) == args["checksum"]:
            ret["success"] = True
            ret["message"] = "Checksum is correct"
            break
    return ret


class SendChatMessage(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter meeting_id is mandatory but missing."},
                status=400
            )
        if "user_name" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter user_name is mandatory but missing."},
                status=400
            )
        if "message" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter message is mandatory but missing."},
                status=400
            )
        send(build_message(args["meeting_id"], args["user_name"], args["message"]))


class StartChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter meeting_id is mandatory but missing."},
                status=400
            )
        if "chat_user" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter chat_user is mandatory but missing."},
                status=400
            )
        if "callback_uri" not in args:
            if "callback_secret" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_uri is mandatory when specifying callback_secret, but missing."
                    },
                    status=400
                )

        if "callback_secret" not in args:
            if "callback_uri" in args:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Parameter callback_secret is mandatory when specifying callback_uri, but missing."
                    },
                    status=400
                )
        chat, created = Chat.objects.get_or_create(
            meeting_id=args["meeting_id"],
            chat_user_name=args["chat_user"],
            callback_uri="" if "callback_uri" not in args else args["callback_uri"],
            callback_secret="" if "callback_secret" not in args else args["callback_secret"],
        )
        if not created:
            return JsonResponse({"success": False, "message": "Chat is already registered"}, status=304)
        chat.save()
        # TODO Register listener
        return JsonResponse({"success": True, "message": "Chat registered successfully"})


class EndChatForMeeting(TemplateView):

    def post(self, request, *args, **kwargs):
        args = json.load(request.POST)
        validated = validate_request(args, "sendChatMessage")
        if not validated["success"]:
            return JsonResponse(validated, status=400)
        if "meeting_id" not in args:
            return JsonResponse(
                {"success": False, "message": " Parameter meeting_id is mandatory but missing."},
                status=400
            )
        try:
            chat = Chat.objects.get(meeting_id=args["meeting_id"])
            chat.delete()
            # TODO Stop listener
        except Chat.DoesNotExist:
            return JsonResponse({"success": False, "message": "Chat was not found"}, status=404)
        return JsonResponse({"success": True, "message": "Chat was successfully ended"})
