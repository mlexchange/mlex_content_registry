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
WEBHOOK_RECEIVER_URL = 'http://%s' % config['webhook']['RECEIVER']
MONGO_DB_URI = "mongodb+srv://admin:%s" % str(os.environ['ATLAS_ACCESS'])

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


def get_content(uid: str):
    url = 'http://content-api:8000/api/v0/contents/{}/content'.format(uid)  # current host, could be inside the docker
    response = requests.get(url).json()
    return response

def workflow_dependency(workflow):
    workflow_list = workflow['workflow_list']
    dependency = {}
    if workflow['workflow_type'] == 'serial':
        for i,work_id in enumerate(workflow_list):
            dependency[work_id] = []
            for j in range(len(workflow_list)):
                if j > i:
                    dependency[work_id].append(workflow_list[j])
    
    elif workflow['workflow_type'] == 'parallel':
        for work_id in workflow_list:
            dependency[work_id] = []
                
    return workflow_list, dependency


# def construct_dependency(uid: str):
#     content = get_content(uid)
#     job_list = []
#     dependencies = {}
#     if content['content_typ'] == 'workflow':
#         workflow_list, workflow_dependency_list = workflow_dependency(content)
#         for workflow_id in workflow_list:
#             if workflow_id not in job_list:
#                 job_list.append(workflow_id)
#                 dependencies[workflow_id] = []
#             dependencies[workflow_id].extend(workflow_dependency_list)


def job_content_dict(content):
    job_content = {'mlex_app': content['name'],
                   'service_type': content['service_type'],
                   'working_directory': '',
                   'job_kwargs': {'uri': content['uri'], 
                                  'cmd': content['cmd'][0]}
                   }
    
    if 'map' in content:
        job_content['job_kwargs']['map'] = content['map']
    
    if 'container_kwargs' in content:
        job_content['job_kwargs']['container_kwargs'] = content['container_kwargs']
    
    return job_content


def send_webhook(msg):
    """
    Send a webhook to a specified URL
    :param msg: task details, dict
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



