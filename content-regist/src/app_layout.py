# #!/usr/bin/env Python3

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash_table

from registry_util import get_content_list

job_list = []
try:
    model_list = get_content_list()
except Exception:
    print("Unable to connect to the server.")

MODEL_KEYS    = ['name', 'version', 'owner', 'type', 'uri', 'description']
APP_KEYS      = ['name', 'version', 'owner', 'uri', 'description']
WORKFLOW_KEYS = ['name', 'version', 'owner', 'workflow_type', 'description']
JOB_KEYS      = ['description', 'service_type', 'submission_time', 'execution_time', 'job_status']

OWNER = 'mlexchange team'

MODEL_TEMPLATE = {
    "content_type": "model",
    "name": "example",
    "public": False,
    "version": "xxx",
    "type": "xxx",
    "owner": OWNER,
    "service_type": "backend",
    "uri": "xxx",
    "reference": "xxx",
    "application": [],
    "description": "xxx",
    "gui_parameters": [],
    "cmd": [],
    "kwargs": {},
    "compute_resources": {'num_processors': 0,
                          'num_gpus': 0}
}

APP_TEMPLATE = {
    "content_type": "app",
    "name": "example",
    "public": False,
    "version": "xxx",
    "owner": OWNER,
    "service_type": "frontend",
    "uri": "xxx",
    "reference": "xxx",
    "application": [],
    "description": "xxx",
    "cmd": [],
    "kwargs": {},
    "compute_resources": {'num_processors': 0,
                          'num_gpus': 0}
}

WORKFLOW_TEMPLATE = {
    "content_type": "workflow",
    "name": "example",
    "public": False,
    "version": "xxx",
    "owner": OWNER,
    "uri": "xxx",
    "reference": "xxx",
    "application": [],
    "workflow_type": "serial",
    "workflow_list": [],
    "description": "xxx",
    "cmd": [],
    "kwargs": {},
}


external_stylesheets = [dbc.themes.BOOTSTRAP, "../assets/segmentation-style.css",]  # need to use bootstrap themes

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#-------------------------------------- function -----------------------------------------
def dash_forms(type):
    forms = [
        dbc.FormGroup(
            [
                dbc.Label("Please give a name for the {}.".format(type)),
                dbc.Input(id="name-regist", type="text", placeholder="Enter {} name.".format(type), debounce=True),
            ],
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the version for the {}.".format(type) ),
                dbc.Input(id="version-regist", type="text", placeholder="Enter {} version.".format(type), debounce=True),
            ],
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the URI for the {}.".format(type) ),
                dbc.Input(id="uri-regist", type="text", placeholder="Enter the URI.", debounce=True),
            ],
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter reference for the {}.".format(type) ),
                dbc.Input(id="reference-regist", type="text", placeholder="Enter reference.",debounce=True),
            ],
        ),
        dbc.FormGroup(
            [ dbc.Label("Enter the commands to deploy the {}. Use comma to separate.".format(type), className="mr-2"),
              dbc.Input(id="cmd-regist", type="text", placeholder="Enter commands to deploy the {}".format(type), debounce=True),
            ],
        ),
        dbc.FormGroup(
            [ dbc.Label("Enter any other kwargs to deploy the {} (optional). Use double quotes to construct the kwargs dictionary.".format(type), className="mr-2"),
              dbc.Input(id="kwargs-regist", type="text", placeholder="Enter kwargs to deploy the {}".format(type), debounce=True),
            ],
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter description (optional) for the {}.".format(type) ),
                dbc.Input(id="description-regist", type="text", placeholder="Enter description.",debounce=True),
            ],
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter application(s) for the {} (e.g., image segmentation). Use comma to separate.".format(type) ),
                dbc.Input(id="application-regist", type="text", placeholder="Enter applications for this {}".format(type),debounce=True),
            ],
        ),
        dbc.FormGroup([
            dbc.Label('Set Accessibility'),
            dbc.RadioItems(
                options=[{'label' : 'private', 'value': False},
                         {'label': 'public', 'value': True}],
                id = 'access-type',
                value = False,
                inline = True,
                labelStyle={'margin': '6px'}
            ),
        ]),
    ]
    return forms



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
                                    html.H3("MLExchange | Content Registry"),
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


MODEL_REGISTRY = html.Div([
    dbc.FormGroup([
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
    ]),
    dbc.FormGroup(
        [   dbc.Label("Resources requirement", className="mr-2"),
            html.Div([
                dbc.Label("CPU", className="mr-2"),
                dbc.Input(id="model-cpu-num", type="number", value=0, className="mr-5"),
                dbc.Label("GPU", className="mr-2"),
                dbc.Input(id="model-gpu-num", type="number", value=0)
              ],
              style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'},
            )
        ]    
    ),
    dbc.Button(
        "+ Add GUI Component",
        id="gui-component-add",
        className="mr-2",
        color="success",
        size="sm",
        style={'width':'40%'},
        n_clicks=0,
    ),
    dbc.Button(
        "Double-click to See GUI Component(s)",
        id="gui-check",
        className="mr-2",
        color="success",
        size="sm",
        style={'width':'55%'},
        n_clicks=0,
    ),
    html.Div(id='dynamic-gui-container', children=[]),
])

APP_REGISTRY = html.Div([
    dbc.FormGroup([
      dbc.Label('App Type'),
      dbc.RadioItems(
          options=[
              {'label': 'frontend', 'value': 'frontend'},
              {'label' : 'backend', 'value': 'backend'},
          ],
          id = 'app-type',
          value = 'frontend',
          inline = True,
          labelStyle={'margin': '6px'}
      ),
    ]),
    dbc.Collapse(
        children=dbc.FormGroup(
            [
                dbc.Label("Please input porting for the frontend app. Use comma to separate if there are more than one."),
                dbc.Input(id="app-port", type="text", placeholder="Enter port_number/method (e.g. 8061/tcp).", debounce=True),
            ],
        ),
        id="collapse-app-port",
        is_open=False,
    ),
    dbc.FormGroup(
            [   dbc.Label("Resources requirement", className="mr-2"),
                html.Div([
                    dbc.Label("CPU", className="mr-2"),
                    dbc.Input(id="app-cpu-num", type="number", placeholder="cpu number", value=0, className="mr-5"),
                    dbc.Label("GPU", className="mr-2"),
                    dbc.Input(id="app-gpu-num", type="number", placeholder="gpu number", value=0)
                ],
                style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'},
              )
            ]    
      )
])

WORKFLOW_REGISTRY = html.Div([
    dbc.FormGroup([
        dbc.Label('Choose wrokflow execution'),
        dbc.RadioItems(
            options=[
                {'label': 'serial', 'value': 'serial'},
                {'label' : 'parallel', 'value': 'parallel'},
            ],
            id = 'workflow-execution-type',
            value = 'serial',
            inline = True,
            labelStyle={'margin': '6px'}
        ),
    ]),
    dbc.FormGroup([
        dbc.Button(
                "+ Add a Content to Form a Workflow",
                id="workflow-group-add",
                className="mr-2",
                color="success",
                size='sm',
                style={'width':'100%'},
                n_clicks=0,
        ),
        html.Div(id='workflow-gui-container', children=[]),
    ]),
])

register_model = dbc.Card(
    id = "register-model-card",
    children = [
        dbc.CardBody(
        [
            html.Div([
                html.Div(
                    [
                        dbc.RadioItems(
                            id="tab-group",
                            className="btn-group",
                            inputClassName="btn-check",
                            labelClassName="btn btn-outline-primary",
                            labelCheckedClassName="active",
                            labelStyle={'font-size': '15px', 'width': '100px', 'margin':'10px'},
                            options=[
                                {"label": "Model", "value": "model"},
                                {"label": "App", "value": "app"},
                                {"label": "Workflow", "value": "workflow"},
                                # {"label": "Resource", "value": "resource"}
                            ],
                            value="model")
                    ],
                    className="radio-group",
                    style ={'display': 'flex', 'justify-content': 'center', 'margin': '10px'},
                ),
                html.Hr(),
                html.Div([
                    #dbc.Label('1.'),
                    dbc.Button(
                        "Generate New Content",
                        id="generate-json",
                        className="mr-1",
                        color="success",
                        size="sm",
                        style={'width':'40%', 'margin': '10px', 'margin-left': '15px'}
                    ),
                    dbc.Label('after filling out the forms below. Then,'),
                    ],
                    className='row',
                    style={'align-items': 'center', 'justify-content': 'left'}
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Register New Content",
                            id="button-register",
                            className="mr-1",
                            color="success",
                            size="sm",
                            n_clicks=0,
                            style={'width':'40%', 'margin-left': '15px', 'margin-right': '15px'}
                        ),
                        dbc.Label('or'),
                        html.Div([
                            html.Button("Download Content Document", id="btn-download-txt"),
                            dcc.Download(id="download-text")
                            ],
                            style={'width':'45%', 'margin-left': '15px'}
                        ),
                    ],
                    className='row',
                    style={'align-items': 'center', 'justify-content': 'left', 'margin-bottom': '20px'}
                ),
                ],
                style={'align-items': 'center', 'justify-content': 'center', 'margin-bottom': '20px'},   
            ),
            html.Div(id='tab-display', children=dbc.Form(children=dash_forms('model'))),
            dbc.Collapse(
                MODEL_REGISTRY,
                id="collapse-model-tab",
                is_open=False,
            ),
            dbc.Collapse(
                APP_REGISTRY,
                id="collapse-app-tab",
                is_open=False,
            ),
            dbc.Collapse(
                WORKFLOW_REGISTRY,
                id="collapse-workflow-tab",
                is_open=False,
            ),
        ],
        ),
    ]
)


data_uploader = dcc.Upload(
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
    # Not allow multiple files to be uploaded
    multiple=False,
)


upload_model = dbc.Card(
    id="upload-model-card",
    children=[
        dbc.CardBody([
            dbc.Form(
                [
                    html.Div(
                        [
                            dbc.Label("Please upload your content document after validation."),
                            dbc.Button(
                                 "Validate Content Document",
                                id="button-validate",
                                className="mr-2",
                                color="success",
                                size="sm",
                                style={'width':'40%', 'margin-top': '10px'}
                            ),
                            dbc.Button(
                                "Upload Content Document",
                                id="button-upload",
                                color="success",
                                size="sm",
                                style={'width':'40%', 'margin-top': '10px'}
                            ),
                        ],
                        className='row',
                        style={'align-items': 'center', 'justify-content': 'center', 'margin-bottom': '20px'}
                    ),
                    html.Div(id='output-json-validation'),
                    dbc.Card([
                        html.Div(id='data-uploader', children = data_uploader),
                        html.Div(id='output-data-upload'),
                    ]),
                ],
            ),
            html.Div(id='gui-layout', children=[])
        ])
    ]
)


#-------------------------------------------------------------------------------------
table_models = dbc.Card(
    id = "table-models",
    children = [
        dbc.CardBody([
            dbc.Button(
                "Refresh Content List",
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
            dbc.Button(
                "Launch the Selected",
                id="button-launch",
                className="mtb-2",
                color="success",
                size="sm",
                n_clicks=0,
            ),
            dbc.Modal(
                [
                    dbc.ModalHeader("Warning"),
                    dbc.ModalBody("Files cannot be recovered after deletion. Do you still want to proceed?"),
                    dbc.ModalFooter([
                        dbc.Button(
                            "Delete", id="confirm-delete", color='danger', outline=False, 
                            className="ms-auto", n_clicks=0
                        ),
                    ]),
                ],
                id="modal",
                is_open=False,
                style = {'color': 'red'}
            ), 
            html.Div(
                children = [
                dash_table.DataTable(
                    id='table-model-list',
                    columns=[{'id': p, 'name': p} for p in MODEL_KEYS],
                    data=model_list,
                    row_selectable='multi',
                    page_size=4,
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


table_jobs = dbc.Card(
    id ='running-jobs',
    children = [
        dbc.CardBody([
            html.Div(
                children = [
                    dbc.Button(
                        "Refresh Job List",
                        id="button-refresh-jobs",
                        className="mtb-2",
                        color="primary",
                        size="sm",
                        n_clicks=0,
                    ),
                    dbc.Button(
                        "Terminate the Selected",
                        id="button-terminate",
                        className="m-2",
                        color="warning",
                        size="sm",
                        n_clicks=0,
                    ),
                    dbc.Collapse(
                        children=[dbc.Button(
                                    "Open the Selected Frontend App(s)",
                                    id="button-open-window",
                                    className="mtb-2",
                                    color="success",
                                    size="sm",
                                    n_clicks=0,
                                  )],
                        id="collapse-open-app",
                        is_open=True,
                    )],
                className='row',
                style={'align-items': 'center', 'margin-left': '1px'}
            ),
            html.Div(
                children = [
                dash_table.DataTable(
                    id='table-job-list',
                    columns=[{'id': p, 'name': p} for p in JOB_KEYS],
                    data=job_list,
                    row_selectable='multi',
                    page_size=4,
                    editable=False,
                    style_cell={'padding': '0.5rem', 'textAlign': 'left'},
                    css=[{"selector": ".show-hide", "rule": "display: none"}],
                    style_table={'height':'10rem', 'overflowY': 'auto'}
                ),
            ])
        ])
    ]
)


# metadata
meta = [
    html.Div(
        id="no-display",
        children=[   
            dcc.Store(id="json-store", data=MODEL_TEMPLATE.copy()),
            dcc.Store(id="nothing", data=''),
            dcc.Store(id="web-urls", data=[]),
            dcc.Store(id="dummy", data=''),
            dcc.Store(id="dummy1", data=''),
            dcc.Store(id="dummy2", data=''),
            dcc.Store(id="table-contents-cache", data=[]),
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
                    dbc.Row(dbc.Col(table_jobs, width=12)),
                    dbc.Row(meta)
                ]
            ),
])


