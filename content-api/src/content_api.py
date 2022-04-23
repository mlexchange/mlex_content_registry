import os
import configparser
import uuid
import pymongo
import urllib.request
import json
from copy import deepcopy
from typing import List, Optional
from fastapi import FastAPI
import requests
from pydantic import BaseModel, ValidationError

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
model_list = list(mycollection.find({}).sort("name",pymongo.ASCENDING))
try:
    print(f"model list:\n{model_list}")
except Exception:
    print("Unable to connect to the server.")



API_URL_PREFIX = "/api/v0"

app = FastAPI(  openapi_url ="/api/lbl-mlexchange/openapi.json",
                docs_url    ="/api/lbl-mlexchange/docs",
                redoc_url   ="/api/lbl-mlexchange/redoc",
             )



#token = requests.get('http://content-user:8001/token1').json()
#print(f'token {token}')

# results = requests.post("http://localhost:8001/token", 
#                         data={"username" : "johndoe", 
#                               "password" : "secret", 
#                               "scope" : "me items"}).json()
# 
# headers = { "Authorization" : "Bearer " + results["access_token"]}
# output = requests.get("http://localhost:8001/users/me/", headers=headers).json()
# 
# print(output)



#------------------ models ----------------------
#url = 'http://localhost:8000/api/v0/models'
@app.get(API_URL_PREFIX+"/models", tags=['models'])
def get_models():
    mycollection = conn_mongodb('models')
    #model_list = list(mycollection.find({}).sort("name",pymongo.ASCENDING))
    return list(mycollection.find({}).collation({'locale':'en'}).sort("name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/models/{uid}/model", tags=['models', 'model'])
def get_model(uid: str):
    mycollection = conn_mongodb('models')
    return mycollection.find_one({"content_id": uid})


@app.get(API_URL_PREFIX+"/models/{uid}/model/{comp_group}/gui_params", tags=['model'])
def get_group_gui_params(uid: str, comp_group: str):
    mycollection = conn_mongodb('models')
    gui_params = mycollection.find_one({"content_id": uid})["gui_parameters"]
    group = []
    for param in gui_params:
        if "comp_group" in param.keys():
            if param["comp_group"] == comp_group:
                new_param = deepcopy(param)
                new_param.pop("comp_group")
                group.append(new_param)

    return group
    
#-------------------- apps ---------------------
@app.get(API_URL_PREFIX+"/apps", tags=['apps'])
def get_apps():
    mycollection = conn_mongodb('apps')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/apps/{uid}/app", tags=['apps', 'app'])
def get_app(uid: str):
    mycollection = conn_mongodb('apps')
    return mycollection.find_one({"content_id": uid})

#--------------------- workflows ------------------------
@app.get(API_URL_PREFIX+"/workflows", tags=['workflows'])
async def get_workflows():
    mycollection = conn_mongodb('workflows')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/workflows/{uid}/workflow", tags=['workflows', 'workflow'])
def get_workflow(uid: str):
    mycollection = conn_mongodb('workflows')
    return mycollection.find_one({"content_id": uid})


#-------------------- assets -----------------------
@app.post(API_URL_PREFIX+"/assets", tags=['assets'])
def add_asset(content: dict):
    """
    Add a single asset.  
      - Args: dict 
    """
    content["_id"] = str(uuid.uuid4())
    content["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb('assets')
    mycollection.insert_one(content)
    return content["content_id"]


@app.get(API_URL_PREFIX+"/assets", tags=['assets'])
def get_assets():
    mycollection = conn_mongodb('assets')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/assets/{uid}/asset", tags=['assets', 'asset'])
def get_asset(uid: str):
    mycollection = conn_mongodb('assets')
    return mycollection.find_one({"content_id": uid})


@app.delete(API_URL_PREFIX+"/assets", tags=['assets'])
def delete_assets(uids: list):
    """
    Delete assets.  
      - Args: a list of content_ids 
    """
    mycollection = conn_mongodb('assets')
    mycollection.delete_many({'content_id':{'$in':uids}})
    
    
