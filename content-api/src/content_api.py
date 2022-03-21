import configparser
import pymongo

from typing import Optional
from fastapi import FastAPI

config = configparser.ConfigParser()
config.read('config.ini')
MONGO_DB_URI = config['content database']['MONGO DB URI']
print(f'MONGO_DB_URI {MONGO_DB_URI}')

#connecting to mongoDB Atlas
def conn_mongodb():
    # set a 10-second connection timeout
    client = pymongo.MongoClient('mongodb+srv://admin:LlDauH4SZIzhs4zL@cluster0.z0jfy.mongodb.net/lbl-mlexchange?retryWrites=true&w=majority', serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    collection = db['models']
    return collection
    
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
async def get_model_list():
    mycollection = conn_mongodb()
    model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
    return model_list