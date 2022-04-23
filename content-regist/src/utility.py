import os
import io
import configparser
import pymongo
import uuid
import urllib.request
import requests
import json
import jsonschema
from jsonschema import validate
from copy import deepcopy


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))
MONGO_DB_URI = "mongodb+srv://admin:%s" % config['content database']['ATLAS_ADMIN']

#connecting to mongoDB Atlas
def conn_mongodb(collection='models'):
    # set a 10-second connection timeout
    client = pymongo.MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    return db[collection]


def get_content_list(collection='models'):
    sort_key = 'content_id'
    mycollection = conn_mongodb(collection)
    return list(mycollection.find({}).collation({'locale':'en'}).sort("name", pymongo.ASCENDING))


def get_dropdown_options(collection='models'):
    contents = get_content_list(collection)
    content_labels = []
    content_values = []
    for content in contents:
        content_labels.append(content["name"]+ "  "+content["version"])
        content_values.append(content["content_id"])
    options = [{'label': item[0], 'value': item[1]} for item in zip(content_labels,content_values)]
    return options


def get_schema(type):
    """
    This function loads the given schema available
    """
    return json.load(io.open('data/{}_schema.json'.format(type), 'r', encoding='utf-8-sig'))


def validate_json(json_data, type):
    """
    REF: https://json-schema.org/ 
    """
    # Describe what kind of json you expect.
    execute_api_schema = get_schema(type)
    try:
        validate(instance=json_data, schema=execute_api_schema)
    except jsonschema.exceptions.ValidationError as err:
        print(f'errr type {type(err)}\n{err}')
        #err = "Given JSON data is invalid"
        return False, err

    message = "Given JSON data is valid."
    return True, message
    
    
def is_duplicate(dict_list,name_str):
    """
    Check if the new model description is already existed on the mongodb.
    """
    found = False
    for i,item in enumerate(dict_list):
        if item["name"] == name_str:
            found = True
            _id = item["_id"]
            uri    = item["uri"]
            description = item["description"]
            break
    if not found:
        return None, None, None, found
    else:
        return _id, uri, description, found 


def update_mongodb(name, uri, description):
    """
    Update model registry by model_name, uri, and description.
    """
    model_list = get_content_list('models')
    if name != "" and name is not None:
        _id, job_uri, job_description, found = is_duplicate(model_list, name)
        if not found:
            _id = str(uuid.uuid4())
            content_id = str(uuid.uuid4())
            mycollection = conn_mongodb()
            mycollection.insert_one({"_id": _id, "content_id": content_id, "name": name, "uri": uri,"description": description})
            print(f"add new model name: {name}")
        else:
            if uri != "" and uri is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": _id},{"$set":{"uri": uri}})
            if description != "" and description is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": _id},{"$set":{"description": description}})


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






