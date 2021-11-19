# #!/usr/bin/env Python3

import io
import re

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output, State, MATCH, ALL

import pymongo
import uuid

import urllib.request
import requests
import json
import base64

import jsonschema
from jsonschema import validate

from targeted_callbacks import targeted_callback
from kwarg_editor import JSONParameterEditor

import plotly.express as px


#------------------------------------- helper functions ----------------------------------
#connecting to mongoDB Atlas
def conn_mongodb():
    conn_str = "mongodb+srv://admin:LlDauH4SZIzhs4zL@cluster0.z0jfy.mongodb.net/lbl-mlexchange?retryWrites=true&w=majority"
    # set a 10-second connection timeout
    client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=100000)
    db = client['lbl-mlexchange']
    collection = db['models']
    return collection
    
mycollection = conn_mongodb()
model_list = list(mycollection.find({}).sort("model_name",pymongo.ASCENDING))
try:
    print(f"model list:\n{model_list}")
except Exception:
    print("Unable to connect to the server.")
    

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


external_stylesheets = [dbc.themes.BOOTSTRAP, "../assets/segmentation-style.css",]  # need to use bootstrap themes

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#--------------------------------------- App layouts -------------------------------------
header= dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.Img(
                            id="logo",
                            src='assets/mlex.png',
                            height="60px",
                        ),
                        md="auto",
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H3("MLExchange | Model Registry"),
                                ],
                                id="app-title",
                            )
                        ],
                        md=True,
                        align="center",
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
    ),
    dark=True,
    color="dark",
    sticky="top",
)


form_regist = dbc.Form(
    [
        dbc.FormGroup(
            [
                dbc.Label("Please give a name for the model.", className="mr-2"),
                dbc.Input(id="name-regist", type="text", placeholder="Enter model name.", debounce=True),
                html.P(id = "regist-response0"), 
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the version for the model.", className="mr-2"),
                dbc.Input(id="version-regist", type="text", placeholder="Enter model version.", debounce=True),
                html.P(id = "regist-response4"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide user name for the model.", className="mr-2"),
                dbc.Input(id="user-regist", type="text", placeholder="Enter user name.", debounce=True),
                html.P(id = "regist-response5"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the URI for the model.", className="mr-2"),
                dbc.Input(id="uri-regist", type="text", placeholder="Enter the URI.", debounce=True),
                html.P(id = "regist-response1"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter reference for the model.", className="mr-2"),
                dbc.Input(id="reference-regist", type="text", placeholder="Enter reference.",debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter description (optional) for the model.", className="mr-2"),
                dbc.Input(id="description-regist", type="text", placeholder="Enter description.",debounce=True),
                html.P(id = "regist-response2"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter application(s) for the model (e.g., image segmentation). Use comma to separate.", className="mr-2"),
                dbc.Input(id="application-regist", type="text", placeholder="Enter applications for this model",debounce=True),
                html.P(id = "regist-response3"),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [   dbc.Label("Enter the commands to deploy the model. Use comma to separate.", className="mr-2"),
                dbc.Input(id="cmd-regist", type="text", placeholder="Enter commands to deploy the model", debounce=True),
            ],
            className="mr-3",
        ),
    ],
)



register_model = dbc.Card(
    id = "register-model-card",
    children = [
        dbc.CardBody(
        [
            dbc.Button(
            "Register New Model",
            id="subbutton0",
            className="mr-1",
            color="success",
            size="sm",
            n_clicks=0,
            ),
            dbc.Button(
            "Update Existing Model",
            id="subbutton1",
            className="mr-1",
            color="warning",
            size="sm",
            n_clicks=0,
            ),
            dbc.Button(
            "Delete Existing Model",
            id="subbutton2",
            className="mr-1",
            color="danger",
            size="sm",
            n_clicks=0,
            ),
            html.Hr(),
            dbc.Form(
            [
                dbc.FormGroup(
                [
                    dbc.Button(
                        "Generate Model Document",
                        id="generate-json",
                        className="mr-1",
                        color="success",
                        size="sm",
                        n_clicks=0,
                        ),
                ]
                ),
                dbc.FormGroup(
                [
                    html.Div([
                        html.Button("Download Model Document", id="btn-download-txt"),
                        dcc.Download(id="download-text")
                    ]),
                ]
                )
                
            ],
            inline=True
            ),
            html.Hr(),
            form_regist,
            dbc.Card(
            [
                dbc.Label('Choose Model Type', className='mr-2'),
                dbc.RadioItems(
                    options=[
                        {'label': 'supervised', 'value': 'supervised'},
                        {'label' : 'unsupervised', 'value': 'unsupervised'},
                    ],
                    id = 'model-type',
                    value = 'supervised',
                    inline = True,
                    labelStyle={'margin': '10px'}
                ),
            ],
            ),
        ],
        ),
        dbc.CardBody([
            dbc.Button(
            "Add GUI Component",
            id="gui-component-add",
            className="mr-1",
            color="success",
            size="sm",
            n_clicks=0,
            ),
            dbc.Button(
            "See GUI Component(s)",
            id="gui-check",
            className="mr-1",
            color="success",
            size="sm",
            n_clicks=0,
            ),
            html.Div(id='dynamic-gui-container', children=[]),
        ]),
    ]
)


upload_model = dbc.Card(
    id="upload-model-card",
    children=[
        dbc.CardBody([
            dbc.Form(
                [
                   dbc.Button(
                        "Validate Model Document",
                        id="button-validate",
                        className="mr-1",
                        color="success",
                        size="sm",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        "Upload Model Document",
                        id="button-upload",
                        className="mr-1",
                        color="success",
                        size="sm",
                        n_clicks=0,
                    ),
                    html.Hr(),
                    dbc.CardBody("Please submit your model document after validation."),
                    html.Div(id='output-json-validation'),
                    dbc.Card(
                        [
                            html.Div([
                                        dcc.Upload(
                                            id='upload-data',
                                            children=html.Div([
                                                'Drag and Drop or ',
                                                html.A('Select Files')
                                            ]),
                                            style={
                                                'width': '95%',
                                                'height': '60px',
                                                'lineHeight': '60px',
                                                'borderWidth': '1px',
                                                'borderStyle': 'dashed',
                                                'borderRadius': '5px',
                                                'textAlign': 'center',
                                                'margin': '10px'
                                            },
                                            # Allow multiple files to be uploaded
                                            multiple=False,
                                        ),
                                        html.Div(id='output-data-upload'),
                                    ]),
                        ],
                    ),
                ],
            ),
            html.Hr(),
            dbc.Card(
            [
                html.H5("GUI layout", className="card-title"),
                html.Div(id='gui-layout',
                        children=[]
                ),
            ])
        ])
    ]
)



#-------------------------------------------------------------------------------------
params = ['model_name', 'version', 'user', 'type', 'uri','description']
table_models = dbc.Card(
    id = "table-models",
    children = [
        dbc.CardBody([
            dbc.Button(
                "Refresh Model List",
                id="button2",
                className="mb-3",
                color="primary",
                n_clicks=0,
            ),
            html.Div([
                dash_table.DataTable(
                id='table-model-list',
                columns=([{'id': p, 'name': p} for p in params]),
                data=model_list,
                editable=False
                ),
            ]),
            #dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True),
        ])
    ]
)


json_file = {
  "model_name": "example",
  "version": "example",
  "type": "example",
  "user": "example",
  "uri": "example",
  "application": [],
  "description": "xxx",
  "gui_parameters": [],
  "cmd": []
}


# metadata
meta = [
    html.Div(
        id="no-display",
        children=[   
            dcc.Store(id="dynamic-json", data=json_file.copy()),
            dcc.Store(id="json-store", data=[]),
            dcc.Store(id="nothing", data=''),
            dcc.Store(id='validation', data=0),
        ],
    ),
]


# Setting up initial webpage layout
app.layout = html.Div (
        [
            header,
            dbc.Container(
                [
                    dbc.Row([dbc.Col(register_model, width=6), dbc.Col(upload_model, width=6)]),
                    dbc.Row(dbc.Col(table_models, width=12)),
                    dbc.Row(meta)
                ]
            ),
])



#----------------------------------- callback reactives ------------------------------------
def model_list_GET_call():
    """
    Get the whole model registry data from the fastapi url.
    """
    url = 'http://model-api:8000/api/v0/model-list'
    #url = 'http://localhost:8000/api/v0/model-list'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data


@app.callback(
    Output("table-model-list", "data"),
    Input("button2", "n_clicks"),
    )
def check_models(n):
    data = model_list_GET_call()
    if n:
        return data
    return data


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
    mycollection = conn_mongodb()
    model_list = list(mycollection.find({}))
    if name != "" and name is not None:
        job_id, job_uri, job_description, found = ifduplicate(model_list, name)
        if not found:
            job_id = str(uuid.uuid4())
            mycollection = conn_mongodb()
            mycollection.insert_one({"_id": job_id, "model_name": name, "uri": uri,"description": description})
            print(f"add new model name: {name}")
        else:
            if uri != "" and uri is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": job_id},{"$set":{"uri": uri}})
            if description != "" and description is not None:
                mycollection = conn_mongodb()
                mycollection.update_one({"_id": job_id},{"$set":{"description": description}})


@app.callback(
    [   Output("regist-response0", "children"),
        Output("regist-response1", "children"),
        Output("regist-response2", "children"),
    ], 
    [   Input("name-regist","value"),
        Input("uri-regist","value"),
        Input("description-regist","value"),
        Input('subbutton0', 'n_clicks'),
        Input('subbutton1', 'n_clicks'),
        Input('subbutton2', 'n_clicks')
    ],
    )
def update_regist(regist_name, regist_uri, regist_description, sub0,sub1,sub2):
    mycollection = conn_mongodb()
    model_list = list(mycollection.find({}))
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    results    = [regist_name, regist_uri, regist_description]
    
    #output messages
    output1 = 'The model name you are looking for does not exist!'
    output2 = 'Please provide a valid model name!'
    
    if 'subbutton0' in changed_id:
        if regist_name != "" and regist_name is not None:
            job_id, job_uri, job_description, found = ifduplicate(model_list,regist_name)
            if all(v is not None for v in [job_id, job_uri, job_description]):
                output = 'The model name is already existed! Please use a differnet name!'
                results = [output for i in range(3)]
            else:
                update_mongodb(regist_name, regist_uri, regist_description)
        else:
            output = 'Please provide a model name!'
            results = [output for i in range(3)]
    
    elif 'subbutton1' in changed_id:
        if regist_name != "" and regist_name is not None:
            job_id, job_uri, job_description, found = ifduplicate(model_list, regist_name)
            if not found:
                results = [output1 for i in range(3)]
            else:
                update_mongodb(regist_name, regist_uri, regist_description)
                results = ['Updating model: ' + str(s) for s in results] 
        else:
            results = [output2 for i in range(3)]
        
    elif 'subbutton2' in changed_id:
        if regist_name != "" and regist_name is not None:
            job_id, job_uri, job_description, found = ifduplicate(model_list, regist_name)
            if not found:
                results = [output1 for i in range(3)]
            else:
                mycollection = conn_mongodb()
                mycollection.delete_one({"model_name": regist_name})
                results = ['Deleting model: ' + str(s) for s in results]
        else:
            results = [output2 for i in range(3)]
            
    return results


@app.callback(
    Output("nothing", "data"),
    Input("button-upload", "n_clicks"),
    Input('validation', 'data'),
    State("json-store", "data"),
    )
def update_models_from_uploads(n, is_valid, data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-upload' in changed_id:
        if bool(data) and is_valid:
            #print(f'return data\n{data}')
            mycollection = conn_mongodb()
            if isinstance(data, list):
                if len(data) == 1:
                    mycollection.insert_one(data[0])
                else:
                    mycollection.insert_many(data)  
            else:
                mycollection.insert_one(data)


@app.callback(
    Output('dynamic-gui-container', 'children'),
    Input('gui-component-add', 'n_clicks'),
    State('dynamic-gui-container', 'children'))
def display_component(n_clicks, children):
    new_element = html.Div([
        dbc.Label("Choose component type:"),
        dcc.Dropdown(
            id={
                'type': 'dynamic-dropdown',
                'index': n_clicks
            },
            options=[{'label': i, 'value': i} for i in ['int', 'float', 'str', 'slider','dropdown','radio','bool','graph']]
        ),
        html.Div(
            id={
                'type': 'dynamic-output',
                'index': n_clicks
            }
        )
    ])
    children.append(new_element)
    return children


#-------------------------------------- dynamic JSON generator ---------------------------
def make_form_input(i):
    form_input = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter name (key)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="text", placeholder="default value"),
        ]
    )
    return form_input

def make_form_slider(i):
    form_slider = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter name (key)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "min"},   type="number", placeholder="min"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "max"},   type="number", placeholder="max"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "step"},  type="number", placeholder="step"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="number", placeholder="default value"),
            dbc.Label("Input marks following: value1, label1, value2, label2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "marks"}, type="text", placeholder="marks"),
        ]
    )
    return form_slider


def make_form_dropdown(i):    
    form_dropdown = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},   type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"},  type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},    type="text", placeholder="parameter name (key)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"},  type="text", placeholder="default value"),
            dbc.Label("Input options following: label1, value1, label2, value2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "options"},type="text", placeholder="options"),
        ]
    )
    return form_dropdown


def make_form_radio(i):
    form_radio = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},    type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"},   type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},     type="text", placeholder="parameter name (key)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"},   type="text", placeholder="default value"),
            dbc.Label("Input options following: label1, value1, label2, value2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "options"}, type="text", placeholder="options"),
        ]
    )
    return form_radio


def make_form_bool(i):
    form_bool = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter name (key)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="text", placeholder="default value"),
        ]
    )
    return form_bool


def make_form_graph(i):
    form_graph = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="unique id"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter name (key)"),
        ]
    )
    return form_graph


@app.callback(
    Output({'type': 'dynamic-output', 'index': MATCH}, 'children'),
    Input({'type': 'dynamic-dropdown', 'index': MATCH}, 'value'),
    State('gui-component-add', 'n_clicks'), # or input
    
    prevent_initial_call = True
)
def display_output(value, n_cliks):
    i = int(re.findall('(?<="index":)\\d+(?=,)', dash.callback_context.triggered[0]['prop_id'])[0])
    if value in ['float','int','str']:
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_input(i)])
    elif value == 'dropdown':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_dropdown(i)])
    elif value == 'slider':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_slider(i)])
    elif value == 'radio':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_radio(i)])
    elif value == 'bool':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_bool(i)])
    elif value == 'graph':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_graph(i)])
    else:
        return ""


@app.callback(
    Output("dynamic-json", "data"),
    Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
    Input("name-regist", "value"),
    Input("version-regist", "value"),
    Input("model-type", "value"),
    Input("user-regist", "value"),
    Input("uri-regist", "value"),
    Input("reference-regist", "value"),
    Input("description-regist", "value"),
    Input("application-regist", "value"),
    Input("cmd-regist", "value"),
    Input('dynamic-gui-container', 'children'),
    Input("generate-json", "n_clicks"),
    Input("gui-check", "n_clicks"),

    prevent_initial_call=True
    )
def json_generator(component_type, name, version, model_type, user, uri, reference, description, applications, cmds, children, n, n_clicks):
    keys = ["model_name","version","type","user","uri","reference", "description"]
    items = [name, version, model_type, user, uri, reference, description]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    #print(f'gui container children\n{children}')
    json_document = json_file.copy()  # shallow copy
    json_document["gui_parameters"] = []  # set the gui parameter list to empty
    if 'generate-json' in changed_id or 'gui-check' in changed_id:
        for item,key in zip(items,keys):
            if bool(item):
                json_document[key] = item

        if bool(applications):
            applications = applications.split(",")
            for application in applications:
                if application not in json_document["application"]:
                    json_document["application"].append(application)
        
        if bool(cmds):
            cmds = cmds.split(",")
            for cmd in cmds:
                if cmd not in json_document["cmd"]:
                    json_document["cmd"].append(cmd)
        
        
        if children[0]['props']['children'][2]['props']['children'] is not None and bool(component_type):
            for k,child in enumerate(children):
                input_items = child['props']['children'][2]['props']['children']['props']['children'][1]['props']['children']
                length = len(input_items)
                component_combo = {"type":component_type[k]}
                for input_item in input_items:
                    if 'value' in input_item['props']:
                        input_type  = input_item["props"]["id"]["subtype"]
                        input_value = input_item["props"]["value"]
                        print(f'subtype is {input_type}, its value is {input_value}')
                        if input_type == 'marks':
                            marks = {}
                            input_value = input_value.split(",")
                            length = len(input_value)
                            for l in range(int(length/2)):
                                marks[input_value[2*l]] = input_value[2*l+1]
                            component_combo[input_type] = marks 
                    
                        elif input_type == 'options':
                            input_value = input_value.split(",")
                            options = []
                            length = len(input_value)
                            for l in range(int(length/2)):
                                options.append({"label":input_value[2*l], "value":input_value[2*l+1]})
                            component_combo[input_type] = options
                        else:
                            component_combo[input_type] = input_value
                    else:
                        print('No value is found in the input form yet')
                json_document["gui_parameters"].append(component_combo)
        else:
            print('No gui component is added!')

    return json_document


# cannot upload duplicate file consecutively, I guess this makes sense
@app.callback(
       Output('json-store', 'data'),
       Input('upload-data', 'contents'),
       State('upload-data', 'filename'),
       State('upload-data', 'last_modified')
    )
def update_uploads(upload_content, file_name, file_date):
    if upload_content is not None:
        #print(list_of_contents)
        data = []
        print(f'upload_content\n{upload_content}')
        upload_content = json.loads(base64.b64decode(upload_content.split(",")[1]))
        job_id = str(uuid.uuid4())
        upload_content["_id"] = job_id
        data.append(upload_content)
        #print(f'data list\n{data}') 
        return data
    else:
        return []


@app.callback(
        [
            Output('output-json-validation', 'children'),
            Output('validation', 'data'),
        ],
        [
            Input("button-validate", "n_clicks"),
            State('json-store', 'data'),
        ]
        )
def validate_json_schema(n, data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-validate' in changed_id:
        if bool(data):
            is_valid, msg = validate_json(data[0])
            return [str(msg),is_valid]
        else:
            return ["", False]
    else:
        return ["", False]


#--------------------------- targeted callbacks to display GUI components-----------------
def show_dynamic_gui_layouts(n_clicks):
    """
    Show GUI components with inputs from the dynamic GUI generator.
    """
    data = dash.callback_context.states["dynamic-json.data"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'gui-check' in changed_id:
        if bool(data):
            print(f'gui parameters data\n{data["gui_parameters"]}')
            item_list = JSONParameterEditor( _id={'type': 'parameter_editor'},   # pattern match _id (base id), name
                                             json_blob=data["gui_parameters"],
                                            )
            item_list.init_callbacks(app)
            return [item_list]
        else:
            return[""]
    else:
        return [""]

targeted_callback(
    show_dynamic_gui_layouts,
    Input("gui-check", "n_clicks"),
    Output("gui-layout", "children"),
    State("dynamic-json", "data"),
    app=app)


def show_gui_layouts(n_clicks):
    data = dash.callback_context.states["json-store.data"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-validate' in changed_id:
        if bool(data):
            is_valid, msg = validate_json(data[0])
            if is_valid:
                item_list = JSONParameterEditor(_id={'type': 'parameter_editor'},   # pattern match _id (base id), name
                                                json_blob=data[0]["gui_parameters"],
                                            )
                item_list.init_callbacks(app)
                return [item_list]
            else:
                return[""]
        else:
            return [""]
    else:
        return [""]

targeted_callback(
    show_gui_layouts,
    Input("button-validate", "n_clicks"),
    Output("gui-layout", "children"),
    State("json-store", "data"),
    app=app)


@app.callback(
    Output("download-text", "data"),
    Input("btn-download-txt", "n_clicks"),
    State("dynamic-json", "data"),
    prevent_initial_call=True,
)
def download_model(n_clicks, data):
    filename = data["model_name"] + "_v" + data["version"]
    return dict(content=json.dumps(data), filename="{}.json".format(filename))



if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051, debug=True)
    print("model registry is up running!")



