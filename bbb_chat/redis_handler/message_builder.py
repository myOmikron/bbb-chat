import time


def build_message(meeting, chat_user_id, user_name, msg):
    msg = {
        "color": "0",
        "correlationId": chat_user_id + "-" + str(_now()),
        "sender": {
            "id": chat_user_id,
            "name": user_name
        },
        "message": msg
    }

    # TODO sanitize msg.message

    header = {
        "name": "SendGroupChatMessageMsg",
        "meetingId": meeting,
        "userId": chat_user_id
    }

    body = {
        "msg": msg,
        "chatId": "MAIN-PUBLIC-GROUP-CHAT"
    }

    return _make_envelope("SendGroupChatMessageMsg", header, body,
                          routing={"meetingId": meeting, "userId": chat_user_id})


def _now():
    """
    Date.now@javascript
    """
    return int(time.time() * 1000)


def _make_envelope(event, header, body, routing=None):
    return {
        "envelope": {
            "name": event,
            "routing": routing or {"sender": "html5-server"},
            "timestamp": _now()
        },
        "core": {
            "header": header,
            "body": body
        }
    }
