import configparser
import os
import uuid
from copy import deepcopy

import pymongo
import requests
from api_util import send_webhook
from fastapi import FastAPI

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
USER_API_PORT = config["user api port"]["USER_API_PORT"]
SEARCH_API_PORT = config["search api port"]["SEARCH_API_PORT"]
MONGO_DB_USERNAME = str(os.environ["MONGO_INITDB_ROOT_USERNAME"])
MONGO_DB_PASSWORD = str(os.environ["MONGO_INITDB_ROOT_PASSWORD"])
MONGO_DB_URI = "mongodb://%s:%s@mongodb:27017/?authSource=admin" % (
    MONGO_DB_USERNAME,
    MONGO_DB_PASSWORD,
)


# connecting to mongoDB Atlas
def conn_mongodb(collection="models"):
    client = pymongo.MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=100000)
    db = client["content_registry"]
    return db[collection]


mycollection = conn_mongodb()
try:
    model_list = list(mycollection.find({}).sort("name", pymongo.ASCENDING))
except Exception:
    print("Unable to connect to the server.")


API_URL_PREFIX = "/api/v0"

app = FastAPI(
    openapi_url="/api/lbl-mlexchange/openapi.json",
    docs_url="/api/lbl-mlexchange/docs",
    redoc_url="/api/lbl-mlexchange/redoc",
)


# ------------------ content ----------------------
@app.get(API_URL_PREFIX + "/contents/{uid}/content", tags=["content"])
def get_content(uid: str):
    found = None
    for coll in ["models", "apps", "workflows", "assets"]:
        found = conn_mongodb(coll).find_one({"content_id": uid})
        if found:
            break
    return found


# ------------------ models ----------------------
# url = 'http://localhost:8000/api/v0/models'
@app.get(API_URL_PREFIX + "/models", tags=["models"])
def get_models():
    mycollection = conn_mongodb("models")
    return list(
        mycollection.find({})
        .collation({"locale": "en"})
        .sort("name", pymongo.ASCENDING)
    )


@app.get(API_URL_PREFIX + "/models/{uid}/model", tags=["models", "model"])
def get_model(uid: str):
    mycollection = conn_mongodb("models")
    return mycollection.find_one({"content_id": uid})


@app.get(API_URL_PREFIX + "/models/{uid}/model/{comp_group}/gui_params", tags=["model"])
def get_group_gui_params(uid: str, comp_group: str):
    mycollection = conn_mongodb("models")
    gui_params = mycollection.find_one({"content_id": uid})["gui_parameters"]
    group = []
    for param in gui_params:
        if "comp_group" in param.keys():
            if param["comp_group"] == comp_group:
                new_param = deepcopy(param)
                new_param.pop("comp_group")
                group.append(new_param)

    return group


# -------------------- apps ---------------------
@app.get(API_URL_PREFIX + "/apps", tags=["apps"])
def get_apps():
    mycollection = conn_mongodb("apps")
    return list(
        mycollection.find({})
        .collation({"locale": "en"})
        .sort("name", pymongo.ASCENDING)
    )


@app.get(API_URL_PREFIX + "/apps/{uid}/app", tags=["apps", "app"])
def get_app(uid: str):
    mycollection = conn_mongodb("apps")
    return mycollection.find_one({"content_id": uid})


# --------------------- workflows ------------------------
@app.get(API_URL_PREFIX + "/workflows", tags=["workflows"])
def get_workflows():
    mycollection = conn_mongodb("workflows")
    return list(
        mycollection.find({})
        .collation({"locale": "en"})
        .sort("name", pymongo.ASCENDING)
    )


@app.get(API_URL_PREFIX + "/workflows/{uid}/workflow", tags=["workflows", "workflow"])
def get_workflow(uid: str):
    mycollection = conn_mongodb("workflows")
    return mycollection.find_one({"content_id": uid})


# -------------------- assets -----------------------
@app.post(API_URL_PREFIX + "/assets", tags=["assets"])
def add_asset(content: dict):
    """
    Add a single asset.
      - Args: dict
    """
    content["_id"] = str(uuid.uuid4())
    content["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb("assets")
    mycollection.insert_one(content)
    send_webhook(
        {
            "event": "add_content",
            "content_id": content["content_id"],
            "content_type": "asset",
        }
    )
    return content["content_id"]


@app.get(API_URL_PREFIX + "/assets", tags=["assets"])
def get_assets():
    mycollection = conn_mongodb("assets")
    return list(
        mycollection.find({})
        .collation({"locale": "en"})
        .sort("name", pymongo.ASCENDING)
    )


@app.get(API_URL_PREFIX + "/assets/{uid}/asset", tags=["assets", "asset"])
def get_asset(uid: str):
    mycollection = conn_mongodb("assets")
    return mycollection.find_one({"content_id": uid})


@app.delete(API_URL_PREFIX + "/assets", tags=["assets"])
def delete_assets(uids: list):
    """
    Delete assets.
      - Args: a list of content_ids
    """
    mycollection = conn_mongodb("assets")
    mycollection.delete_many({"content_id": {"$in": uids}})
    for uid in uids:
        send_webhook(
            {"event": "delete_content", "content_id": uid, "content_type": "asset"}
        )


# ----------------------- webhook --------------------------
search_keys = [
    "name",
    "version",
    "type",
    "uri",
    "application",
    "reference",
    "description",
    "content_type",
    "content_id",
    "owner",
]
user_keys = ["name", "owner", "content_type", "content_id", "public"]


@app.post(API_URL_PREFIX + "/receiver", status_code=201, tags=["Webhook"])
def webhook_receiver(msg: dict):
    content_id = msg["content_id"]
    content_type = msg["content_type"]
    params = {"index": content_type, "doc_id": content_id}
    if msg["event"] == "add_content":
        content = requests.get(
            f"http://content-api:8000/api/v0/contents/{content_id}/content"
        ).json()
        search_data = {}
        user_data = {}
        for key, value in content.items():
            if key in search_keys:
                search_data[key] = value
            if key in user_keys:
                if key == "content_type":
                    user_data["type"] = value
                elif key == "content_id":
                    user_data["content_uid"] = value
                else:
                    user_data[key] = value

        try:
            requests.post(
                f"http://search-api:{SEARCH_API_PORT}/api/v0/index/document",
                params=params,
                json=search_data,
            )
            # requests.post(f'http://user-api:{USER_API_PORT}/api/v0/content', json = user_data)
        except Exception as err:
            print(
                f"Post request to search api is failed. {err}. Check if search-api is up."
            )

    elif msg["event"] == "delete_content":
        try:
            requests.delete(
                f"http://search-api:{SEARCH_API_PORT}/api/v0/index/{content_type}/document/{content_id}"
            )
            # requests.delete(f'http://user-api:{USER_API_PORT}/api/v0/content/{content_id}')
        except Exception as err:
            print(
                f"Delete request to search api is failed. {err}. Check if search-api is up."
            )
