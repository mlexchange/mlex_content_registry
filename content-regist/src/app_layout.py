# #!/usr/bin/env Python3

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash_table

from utility import get_content_list


model_list = get_content_list()
try:
    print(f"model list:\n{model_list}")
except Exception:
    print("Unable to connect to the server.")

MODEL_KEYS    = ['name', 'version', 'owner', 'type', 'uri','description']
APP_KEYS      = ['name', 'version', 'owner', 'content_id', 'uri','description']
WORKFLOW_KEYS = ['name', 'version', 'owner', 'description']

OWNER = 'mlexchange team'

MODEL_TEMPLATE = {
    "content_type": "model",
    "name": "example",
    "version": "xxx",
    "type": "xxx",
    "owner": OWNER,
    "uri": "xxx",
    "application": [],
    "description": "xxx",
    "gui_parameters": [],
    "cmd": []
}

APP_TEMPLATE = {
    "content_type": "app",
    "name": "example",
    "version": "xxx",
    "owner": OWNER,
    "uri": "xxx",
    "application": [],
    "description": "xxx"
}

WORKFLOW_TEMPLATE = {
    "content_type": "workflow",
    "name": "example",
    "version": "xxx",
    "owner": OWNER,
    "uri": "xxx",
    "application": [],
    "dependency": [],
    "description": "xxx",
}


external_stylesheets = [dbc.themes.BOOTSTRAP, "../assets/segmentation-style.css",]  # need to use bootstrap themes

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#-------------------------------------- function -----------------------------------------
def dash_forms(type):
    forms = [
        dbc.FormGroup(
            [
                dbc.Label("Please give a name for the {}.".format(type), className="mr-2"),
                dbc.Input(id="name-regist", type="text", placeholder="Enter {} name.".format(type), debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the version for the {}.".format(type), className="mr-2"),
                dbc.Input(id="version-regist", type="text", placeholder="Enter {} version.".format(type), debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide user name for the {}.".format(type), className="mr-2"),
                dbc.Input(id="user-regist", type="text", placeholder="Enter user name.", debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Please provide the URI for the {}.".format(type), className="mr-2"),
                dbc.Input(id="uri-regist", type="text", placeholder="Enter the URI.", debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter reference for the {}.".format(type), className="mr-2"),
                dbc.Input(id="reference-regist", type="text", placeholder="Enter reference.",debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter description (optional) for the {}.".format(type), className="mr-2"),
                dbc.Input(id="description-regist", type="text", placeholder="Enter description.",debounce=True),
            ],
            className="mr-3",
        ),
        dbc.FormGroup(
            [
                dbc.Label("Enter application(s) for the {} (e.g., image segmentation). Use comma to separate.".format(type), className="mr-2"),
                dbc.Input(id="application-regist", type="text", placeholder="Enter applications for this {}".format(type),debounce=True),
            ],
            className="mr-3",
        )
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
    dbc.Form([
        dbc.FormGroup(
            [   dbc.Label("Enter the commands to deploy the model. Use comma to separate.", className="mr-2"),
                dbc.Input(id="cmd-regist", type="text", placeholder="Enter commands to deploy the model", debounce=True),
            ],
            className="mr-3"
        )
    ]),
    dbc.Card([
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
])

WORKFLOW_REGISTRY = html.Div([
    dbc.Form([
        dbc.FormGroup(
            [   dbc.Label("Enter the app dependencies (content_ids in APP table) for the workflow. Use comma to separate each app ids. \
                           Use semicolon to separate ids that can be executed in parallel.", className="mr-2"),
                dbc.Input(id="workflow-dependencies", type="text", placeholder="Enter app dependencies", debounce=True),
            ],
            className="mr-3"
        )
    ])
])

register_model = dbc.Card(
    id = "register-model-card",
    children = [
        dbc.CardBody(
        [
            html.Div([
                html.Div([
                    dbc.Button(
                        "Register New Content",
                        id="button-register",
                        className="mr-1",
                        color="success",
                        size="sm",
                        n_clicks=0,
                        style={'width':'40%'}
                    ),
                    dbc.Button(
                        "Update Existing Content",
                        id="button-update",
                        className="mr-1",
                        color="warning",
                        size="sm",
                        n_clicks=0,
                        style={'width':'40%'}
                    )],
                    className='row',
                    style={'align-items': 'center', 'justify-content': 'center'}
                ),
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Generate Content Document",
                            id="generate-json",
                            className="mr-2",
                            color="success",
                            size="sm",
                            style={'width':'40%'}
                        ),
                        html.Div([
                            html.Button("Download Content Document", id="btn-download-txt"),
                            dcc.Download(id="download-text")
                        ]),
                    ],
                    className='row',
                    style={'align-items': 'center', 'justify-content': 'center', 'margin-bottom': '20px'}
                ),
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
                            ],
                            value="model")
                    ],
                    className="radio-group",
                    style ={'margin-bottom': '10px'},
                ),
                #MODEL_REGISTRY,
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
                            dbc.Button(
                                 "Validate Content Document",
                                id="button-validate",
                                className="mr-2",
                                color="success",
                                size="sm",
                                style={'width':'40%'}
                            ),
                            dbc.Button(
                                "Upload Content Document",
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
                    dbc.CardBody("Please upload your content document after validation."),
                    html.Div(id='output-json-validation'),
                    dbc.Card([
                        html.Div(id='data-uploader', children = data_uploader),
                        html.Div(id='output-data-upload'),
                    ]),
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
            dcc.Store(id="json-store", data=MODEL_TEMPLATE.copy()),
            dcc.Store(id="nothing", data=''),
            dcc.Store(id="table-contents-cache", data=[]),
            dcc.Store(id='validation', data=0)
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


