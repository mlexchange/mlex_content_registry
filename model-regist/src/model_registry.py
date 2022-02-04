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
import json
import base64

from utility import conn_mongodb, get_model_list, get_schema, validate_json, ifduplicate, update_mongodb
from generator import make_form_input, make_form_slider, make_form_dropdown, make_form_radio, \
                      make_form_bool, make_form_graph

from targeted_callbacks import targeted_callback
from kwarg_editor import JSONParameterEditor

import plotly.express as px


model_list = get_model_list()
try:
    print(f"model list:\n{model_list}")
except Exception:
    print("Unable to connect to the server.")


FILE_TEMPLATE = {
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
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the version for the model.", className="mr-2"),
                dbc.Input(id="version-regist", type="text", placeholder="Enter model version.", debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide user name for the model.", className="mr-2"),
                dbc.Input(id="user-regist", type="text", placeholder="Enter user name.", debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the URI for the model.", className="mr-2"),
                dbc.Input(id="uri-regist", type="text", placeholder="Enter the URI.", debounce=True),
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
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter application(s) for the model (e.g., image segmentation). Use comma to separate.", className="mr-2"),
                dbc.Input(id="application-regist", type="text", placeholder="Enter applications for this model",debounce=True),
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
             html.Div([
                dbc.Button(
                "Register New Model",
                id="button-register",
                className="mr-1",
                color="success",
                size="sm",
                n_clicks=0,
                style={'width':'40%'}
                ),
                dbc.Button(
                "Update Existing Model",
                id="button-update",
                className="mr-1",
                color="warning",
                size="sm",
                n_clicks=0,
                style={'width':'40%'})
                ],
                className='row',
                style={'align-items': 'center', 'justify-content': 'center'}
            ),
            html.Hr(),
            html.Div(
                [
                    dbc.Button(
                        "Generate Model Document",
                        id="generate-json",
                        className="mr-2",
                        color="success",
                        size="sm",
                        style={'width':'40%'}
                    ),
                    html.Div([
                        html.Button("Download Model Document", id="btn-download-txt"),
                        dcc.Download(id="download-text")
                    ]),
                ],
                className='row',
                style={'align-items': 'center', 'justify-content': 'center'}
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
                    labelStyle={'margin': '6px'}
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
            style={'width':'40%'},
            n_clicks=0,
            ),
            dbc.Button(
            "See GUI Component(s)",
            id="gui-check",
            className="mr-1",
            color="success",
            size="sm",
            style={'width':'40%'},
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
                    html.Div(
                        [
                            dbc.Button(
                                 "Validate Model Document",
                                id="button-validate",
                                className="mr-2",
                                color="success",
                                size="sm",
                                style={'width':'40%'}
                            ),
                            dbc.Button(
                                "Upload Model Document",
                                id="button-upload",
                                color="success",
                                size="sm",
                                style={'width':'40%'}
                            ),
                        ],
                        className='row',
                        style={'align-items': 'center', 'justify-content': 'center'}
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
                #dbc.CardHeader("GUI layout"),
                html.H5("GUI Layout", className="card-title"),
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
                id="button-refresh",
                className="mtb-2",
                color="primary",
                size="sm",
                n_clicks=0,
            ),
            dbc.Button(
                "Delete the Selected",
                id="button-delete",
                className="m-2",
                color="danger",
                size="sm",
                n_clicks=0,
            ),
            html.Div(
                children = [
                dash_table.DataTable(
                    id='table-model-list',
                    columns=([{'id': p, 'name': p} for p in params]),
                    data=model_list,
                    row_selectable='multi',
                    editable=False,
                    style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                    css=[{"selector": ".show-hide", "rule": "display: none"}],
                    style_table={'height':'10rem', 'overflowY': 'auto'}
                ),
            ]),
            #dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True),
        ])
    ]
)


# metadata
meta = [
    html.Div(
        id="no-display",
        children=[   
            dcc.Store(id="dynamic-json", data=FILE_TEMPLATE.copy()),
            dcc.Store(id="json-store", data=[]),
            dcc.Store(id="nothing", data=''),
            dcc.Store(id="models", data=[]),
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
@app.callback(
    Output("table-model-list", "data"),
    Input("button-refresh", "n_clicks"),
    Input('models', 'data')
    )
def refresh_models(n_cliks, data):
    model_list = data
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-refresh' in changed_id:
        model_list = get_model_list()
    
    return model_list


@app.callback( 
    Output("models", "data"),
    [   
        Input("name-regist","value"),
        Input("uri-regist","value"),
        Input("description-regist","value"),
        Input('table-model-list', 'selected_rows'),
        Input('button-register', 'n_clicks'),
        Input('button-update', 'n_clicks'),
        Input('button-delete', 'n_clicks')
    ],
    )
def update_regist(regist_name, regist_uri, regist_description, rows, sub0, sub1, sub2):
    model_list = get_model_list()
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    #output messages
    output = ''
    output1 = 'The model name you are looking for does not exist!'
    output2 = 'Please provide a valid model name!'
    
    if 'button-register' in changed_id:
        if regist_name != "" and regist_name is not None:
            job_id, job_uri, job_description, found = ifduplicate(model_list,regist_name)
            if all(v is not None for v in [job_id, job_uri, job_description]):
                output = 'The model name is already existed! Please use a differnet name!'
            else:
                update_mongodb(regist_name, regist_uri, regist_description)
        else:
            output = 'Please provide a model name!'
    
    if 'button-update' in changed_id:
        if regist_name != "" and regist_name is not None:
            job_id, job_uri, job_description, found = ifduplicate(model_list, regist_name)
            if not found:
                output = output1
            else:
                update_mongodb(regist_name, regist_uri, regist_description)
        else:
            output = output2
        
    if 'button-delete' in changed_id:
        if bool(rows):
            job_ids = [] 
            for row in rows:
                if 'job_id' in model_list[row]:
                    job_ids.append(model_list[row]['job_id'])

            for job_id in job_ids:
                mycollection = conn_mongodb() 
                mycollection.delete_one({"job_id": job_id})

    model_list = get_model_list()
    return model_list


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
    json_document = FILE_TEMPLATE.copy()  # shallow copy
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



