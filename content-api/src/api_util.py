import configparser
import os

import requests

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
WEBHOOK_RECEIVER_URL = "http://%s" % config["webhook"]["RECEIVER"]


def send_webhook(msg):
    """
    Send a webhook to a specified URL
    :param msg: task details
    :return:
    """
    try:
        # Post a webhook message
        resp = requests.post(
            WEBHOOK_RECEIVER_URL,
            json=msg,
            headers={"Content-Type": "application/json"},
            timeout=1.0,
        )
        # Returns an HTTPError if an error has occurred
        # during the process (used for debugging).
        resp.raise_for_status()
    except Exception as err:
        print(err)
        return False
    else:
        return resp.ok
