import os
import configparser
import uuid
import pymongo

from typing import Optional
from fastapi import FastAPI

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
MONGO_DB_URI = "mongodb+srv://admin:%s" % config['content database']['ATLAS_ADMIN']

#connecting to mongoDB Atlas
def conn_mongodb(collection='models'):
    # set a 10-second connection timeout
    #client = pymongo.MongoClient(srvServiceName=MONGO_DB_URI, serverSelectionTimeoutMS=100000)
    client = pymongo.MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    return db[collection]
    
mycollection = conn_mongodb()
model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
try:
    print(f"model list:\n{model_list}")
except Exception:
    print("Unable to connect to the server.")


API_URL_PREFIX = "/api/v0"

app = FastAPI(  openapi_url ="/api/lbl-mlexchange/openapi.json",
                docs_url    ="/api/lbl-mlexchange/docs",
                redoc_url   ="/api/lbl-mlexchange/redoc",
             )


def remove_key_from_dict_list(data, key):
    new_data = []
    for item in data:
        if key in item:
            new_item = deepcopy(item)
            new_item.pop(key)
            new_data.append(new_item)
        else:
            new_data.append(item)

    return new_data

#----------------- utilities -------------------
@app.get(API_URL_PREFIX+"/models/{uid}/model/{comp_group}/gui_params", tags=['model'])
def get_model_gui_params(uid: str, comp_group: str):
    mycollection = conn_mongodb('models')
    return remove_key_from_dict_list(mycollection.find_one({"content_id": uid}), comp_group)


#------------------ models ----------------------
@app.get(API_URL_PREFIX+"/models", tags=['models'])
def get_models():
    mycollection = conn_mongodb('models')
    #model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/models/{uid}/model", tags=['models', 'model'])
def get_model(uid: str):
    mycollection = conn_mongodb('models')
    return mycollection.find_one({"content_id": uid})
    
#-------------------- apps ---------------------
@app.get(API_URL_PREFIX+"/apps", tags=['apps'])
def get_apps():
    mycollection = conn_mongodb('apps')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/apps/{uid}/app", tags=['apps', 'app'])
def get_app(uid: str):
    mycollection = conn_mongodb('apps')
    return mycollection.find_one({"content_id": uid})

#--------------------- workflows ------------------------
@app.get(API_URL_PREFIX+"/workflows", tags=['workflows'])
async def get_workflows():
    mycollection = conn_mongodb('workflows')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/workflows/{uid}/workflow", tags=['workflows', 'workflow'])
def get_workflow(uid: str):
    mycollection = conn_mongodb('workflows')
    return mycollection.find_one({"content_id": uid})


#-------------------- assets -----------------------
@app.post(API_URL_PREFIX+"/assets", tags=['assets'])
def add_models(data: list):
    for content in data:
        content["_id"] = str(uuid.uuid4())
        content["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb('assets')
    return mycollection.insert_many(data)
    
    
@app.post(API_URL_PREFIX+"/assets/{uid}/asset", tags=['assets', 'asset'])
def add_model(uid: str, data: dict):
    data["_id"] = str(uuid.uuid4())
    data["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb('assets')
    return mycollection.insert_one(data)


@app.get(API_URL_PREFIX+"/assets", tags=['assets'])
def get_workflows():
    mycollection = conn_mongodb('assets', tags=['assets'])
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/assets/{uid}/asset", tags=['assets', 'asset'])
def get_workflow(uid: str):
    mycollection = conn_mongodb('assets')
    return mycollection.find_one({"content_id": uid})


@app.delete(API_URL_PREFIX+"/assets", tags=['assets'])
def delete_models(query):
    mycollection = conn_mongodb('assets')
    return mycollection.delete_many(query)
    
    
@app.delete(API_URL_PREFIX+"/assets/{uid}/asset", tags=['assets', 'asset'])
def delete_model(uid: str):
    mycollection = conn_mongodb('assets')
    return mycollection.delete_one({"content_id": uid})
    
    
    
