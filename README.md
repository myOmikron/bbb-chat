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

See [bbb-stream](https://github.com/myOmikron/bbb-stream/blob/master/chat_bridges.md)

### Authentication

See [Random Checksum Protocol](https://github.com/myOmikron/rcp)

In `settings.py`:
```python
SHARED_SECRET = "change_me"
SHARED_SECRET_TIME_DELTA = 5
```
