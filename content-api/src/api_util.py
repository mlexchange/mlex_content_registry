import os
import configparser
import requests

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
WEBHOOK_RECEIVER_URL = 'http://%s' % config['webhook']['RECEIVER']

def send_webhook(msg):
    """
    Send a webhook to a specified URL
    :param msg: task details
    :return:
    """
    try:
        # Post a webhook message
        # default is a function applied to objects that are not serializable = it converts them to str
        resp = requests.post(WEBHOOK_RECEIVER_URL, json=msg, headers={'Content-Type': 'application/json'}, timeout=1.0)
        # Returns an HTTPError if an error has occurred during the process (used for debugging).
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        #print("An HTTP Error occurred",repr(err))
        pass
    except requests.exceptions.ConnectionError as err:
        #print("An Error Connecting to the API occurred", repr(err))
        pass
    except requests.exceptions.Timeout as err:
        #print("A Timeout Error occurred", repr(err))
        pass
    except requests.exceptions.RequestException as err:
        #print("An Unknown Error occurred", repr(err))
        pass
    except:
        pass
    else:
        return resp.status_code
