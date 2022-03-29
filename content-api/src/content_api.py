import configparser
import uuid
import pymongo

from typing import Optional
from fastapi import FastAPI

config = configparser.ConfigParser()
config.read('config.ini')
MONGO_DB_URI = config['content database']['MONGO DB URI']
MONGO_DB_URI = "mongodb+srv://admin:LlDauH4SZIzhs4zL@cluster0.z0jfy.mongodb.net/lbl-mlexchange?retryWrites=true&w=majority"

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


@app.get(API_URL_PREFIX+"/models")
async def get_models():
    mycollection = conn_mongodb('models')
    #model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/models/{uid}")
async def get_model(uid: str):
    mycollection = conn_mongodb('models')
    return mycollection.find_one({"content_id": uid})
    

@app.get(API_URL_PREFIX+"/apps")
async def get_apps():
    mycollection = conn_mongodb('apps')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/apps/{uid}")
async def get_app(uid: str):
    mycollection = conn_mongodb('apps')
    return mycollection.find_one({"content_id": uid})


@app.get(API_URL_PREFIX+"/workflows")
async def get_workflows():
    mycollection = conn_mongodb('workflows')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/workflows/{uid}")
async def get_workflow(uid: str):
    mycollection = conn_mongodb('workflows')
    return mycollection.find_one({"content_id": uid})


#--------------------------------------- assets ------------------------------------------
@app.post(API_URL_PREFIX+"/assets")
async def add_models(data: list):
    for content in data:
        content["_id"] = str(uuid.uuid4())
        content["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb('assets')
    return mycollection.insert_many(data)
    
    
@app.post(API_URL_PREFIX+"/assets/{uid}")
async def add_model(uid: str, data: dict):
    data["_id"] = str(uuid.uuid4())
    data["content_id"] = str(uuid.uuid4())
    mycollection = conn_mongodb('assets')
    return mycollection.insert_one(data)


@app.get(API_URL_PREFIX+"/assets")
async def get_workflows():
    mycollection = conn_mongodb('assets')
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))


@app.get(API_URL_PREFIX+"/assets/{uid}")
async def get_workflow(uid: str):
    mycollection = conn_mongodb('assets')
    return mycollection.find_one({"content_id": uid})


@app.delete(API_URL_PREFIX+"/assets")
async def delete_models(query):
    mycollection = conn_mongodb('assets')
    return mycollection.delete_many(query)
    
    
@app.delete(API_URL_PREFIX+"/assets/{uid}")
async def delete_model(uid: str):
    mycollection = conn_mongodb('assets')
    return mycollection.delete_one({"content_id": uid})
    
    
    
