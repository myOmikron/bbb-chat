# BBB-Chat

This project exposes parts of the ability to chat in BBB via HTTP. 
There's still the need for a user logged in a meeting, which username we're using to send messages.

You're also able to receive messages. Just add a callback handler to the API call and you'll receive the messages of a 
given room.

## Installation
This project has to be deployed on the same server as BBB runs on to gain access to redis.
Therefore, as Ubuntu 16.04 only has access to Python3.5, we need to install a Python Version > 3.5. 
For tests Python 3.9.2 was used, but the project should be fine with anything above 3.5. 

We included an ansible playbook for installing this application. If you're using another Python version,
make sure to correct this in the playbook as well as in the `bbb-chat.service` file. 

## API

### Authentication
In order to have a strong authentication with easy deployment, this project is using a checksum consisting of a shared
secret, and a time factor (unix-epoch). As of the time based component, the use of a NTP Server is highly recommended.

All API calls require this mechanism.

In `settings.py`:
```python
SHARED_SECRET = "change_me"
SHARED_SECRET_TIME_DELTA = 5
```

#### Example

```python
import json
import hashlib
from datetime import datetime

import requests

# Shared secret from bbb-chat
SHARED_SECRET = "change_me"

# Your dictionary with all your parameters
param_dict = {
    "meeting_id": "12345678901234567890-123456789"
}
# Encode as json
json_encoded = json.dumps(param_dict)

# Add API Call
call = "endChatForMeeting" + json_encoded

# Hash with shared secret and current unix epoch
param_dict["checksum"] = hashlib.sha512((call + SHARED_SECRET + str(int(datetime.now().timestamp()))).encode("utf-8")).hexdigest()

# Make request
requests.post("https://example.com/api/endChatForMeeting", data=json.dumps(param_dict))

```

### startChatForMeeting
- Method: `POST`

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
meeting_id       | Yes      | str   | internalMeetingId, returned by `create` call
chat_user        | Yes      | str   | Name of user to send messages with. The user has to join itself.
callback_uri     | No       | str   | Only required when callbacks should be enabled. Specifies the uri to which all messages from the bbb chat should be forwarded to.
callback_secret  | No       | str   | Only required when callbacks should be enabled. Specifies the shared secret to use for a specific callback uri.

The callbacks are sent as `POST` calls with the same checksum method as is used in this project. 
The parameter `callback_secret` specifies the shared secret of the given `callback_uri`. 

### endChatForMeeting
- Method: `POST`

The chat services for the given internalMeetingId are stopped and all information like `callback_secret`, etc. are
deleted in the db.

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
meeting_id       | Yes      | str   | internalMeetingId, returned by `create` call

### sendChatMessage/<meeting_id>
- Method: `POST`

Sends a message from a user_name to a given meeting_id. startChatForMeeting has to be called before sendMessage can be called.

Parameter        | Required | Type  | Description
:---:            | :---:    | :---: | :---:
user_name        | Yes      | str   | Username from which the message was sent
message          | Yes      | str   | Unformatted message
