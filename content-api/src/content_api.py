import configparser
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
#mycollection.insert_one({"_id": job_id, "model_name": "xxx", "uri": "http://localhost", "description": ""})
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
    mycollection = conn_mongodb()
    #model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
    
    
@app.get(API_URL_PREFIX+"/models/{uid}")
async def get_model(uid: str):
    mycollection = conn_mongodb()
    return mycollection.find_one({"_id": uid})
    
    
# @app.post(API_URL_PREFIX+"/models")
# async def add_models():
#     mycollection = conn_mongodb()
#     #model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
#     return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
#     
#     
# @app.post(API_URL_PREFIX+"/models/{uid}")
# async def add_model(uid: str):
#     mycollection = conn_mongodb()
#     return mycollection.insert_one({"_id": uid})
    

# @app.delete(API_URL_PREFIX+"/models")
# async def delete_models():
#     mycollection = conn_mongodb()
#     #model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
#     return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))
#     
#     
# @app.delete(API_URL_PREFIX+"/models/{uid}")
# async def delete_model(uid: str):
#     mycollection = conn_mongodb()
#     return mycollection.find_one({"_id": uid})