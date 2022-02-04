import io
import pymongo
import uuid
import urllib.request
import requests
import json
import jsonschema
from jsonschema import validate


def model_list_GET_call():
    """
    Get the whole model registry data from the fastapi url.
    """
    url = 'http://model-api:8000/api/v0/model-list'
    #url = 'http://localhost:8000/api/v0/model-list'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data


#connecting to mongoDB Atlas
def conn_mongodb():
    conn_str = "mongodb+srv://admin:LlDauH4SZIzhs4zL@cluster0.z0jfy.mongodb.net/lbl-mlexchange?retryWrites=true&w=majority"
    # set a 10-second connection timeout
    client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    collection = db['models']
    return collection


def get_model_list():
    mycollection = conn_mongodb()
    return list(mycollection.find({}).collation({'locale':'en'}).sort("model_name", pymongo.ASCENDING))


def get_schema():
    """
    This function loads the given schema available
    """
    schema = json.load(io.open('data/model_schema.json', 'r', encoding='utf-8-sig'))
    return schema


def validate_json(json_data):
    """
    REF: https://json-schema.org/ 
    """
    # Describe what kind of json you expect.
    execute_api_schema = get_schema()
    try:
        validate(instance=json_data, schema=execute_api_schema)
    except jsonschema.exceptions.ValidationError as err:
        print(f'errr type {type(err)}\n{err}')
        #err = "Given JSON data is invalid"
        return False, err

    message = "Given JSON data is valid."
    return True, message
    
    
def ifduplicate(dict_list,name_str):
    """
    Check if the new model description is already existed on the mongodb.
    """
    found = False
    for i,item in enumerate(dict_list):
        if item["model_name"] == name_str:
            found = True
            job_id = item["_id"]
            uri    = item["uri"]
            description = item["description"]
            break
    if not found:
        return None, None, None, found
    else:
        return job_id, uri, description, found 


def update_mongodb(name, uri, description):
    """
    Update model registry by model_name, uri, and description.
    """
    model_list = get_model_list()
    if name != "" and name is not None:
        _id, job_uri, job_description, found = ifduplicate(model_list, name)
        if not found:
            _id = str(uuid.uuid4())
            job_id = str(uuid.uuid4())
            mycollection = conn_mongodb()
            mycollection.insert_one({"_id": _id, "job_id": job_id, "model_name": name, "uri": uri,"description": description})
            print(f"add new model name: {name}")
        else:
            if uri != "" and uri is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": _id},{"$set":{"uri": uri}})
            if description != "" and description is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": _id},{"$set":{"description": description}})


