# #!/usr/bin/env Python3

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import urllib.request
import requests
import json

from kwarg_editor import JSONParameterEditor

# globle variables


button_model_registry = dbc.Button(
    "View model registry",
    outline=True,
    color="primary",
    href="http://127.0.0.1:8051",
    id="button1",
    style={"text-transform": "none"},
)

button_seg_demo = dbc.Button(
    "View segmentation demo",
    outline=True,
    color="primary",
    href="http://127.0.0.1:8050",
    id="button2",
    style={"text-transform": "none"},
)

button_1d_xray = dbc.Button(
    "View 1d-Xray demo",
    outline=True,
    color="primary",
    #href="http://localhost:8052",
    id="button3",
    style={"text-transform": "none"},
)




external_stylesheets = [dbc.themes.BOOTSTRAP, "../assets/segmentation-style.css"]  # need to use bootstrap themes

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

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
                                    html.H3("MLExchange | Services"),
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


card1 = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Model Registry", className="card-title"),
            #html.P("This card has some text content, but not much else"),
            button_model_registry,
        ]
    )
)


card2 = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Application Demos", className="card-title"),
            dbc.ButtonGroup(
            [
                button_seg_demo,
                button_1d_xray,
            ],
            vertical=True,
        ),
        ]
    )
)


card3 = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Search Model", className="card-title"),
            dbc.Label("Search by model name, user, and application. If no keyword is provided, show full model list.", className="mr-2"),
            dbc.Form(
                [
                    
                    dbc.FormGroup(
                        [
                            dbc.Input(id="model-name-input", type="text", placeholder="Enter model name"),
                        ],
                        className="mr-3",
                    ),
                    dbc.FormGroup(
                        [
                            dbc.Input(id="model-user-input", type="text", placeholder="Enter user"),
                        ],
                        className="mr-3",
                    ),
                    dbc.FormGroup(
                        [
                            dbc.Input(id="model-application-input", type="text", placeholder="Enter application"),
                        ],
                        className="mr-3",
                    ),
                    dbc.Button(
                        "Search",
                        id="search-button",
                        className="mb-1",
                        color="primary",
                        size="sm",
                        n_clicks=0,
                    ),
                ],
                inline=True,
            ),
            
            html.Div([
                "Available models based on the search",
                dcc.Dropdown(id="search-dropdown")
            ]),
           
            html.Hr(),
            html.H5("GUI layout", className="card-title"),
            html.Div(id='model-gui',
                    children=[]
            ),
        ]
    )
)


def model_list_GET_call():
    url = 'http://service-api:8000/api/v0/model-list'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data

@app.callback(
    Output("search-dropdown", "options"),
    Input("search-button", "n_clicks"),
    Input("model-name-input", "value"),
    Input("model-user-input", "value"),
    Input("model-application-input", "value")
    )
def check_search_results(n, model_name, user, application):
    if n:
        data = model_list_GET_call()
        print(f'model_name: {model_name}, user: {user}')
        if model_name is not None and model_name != '':
            data = [d for d in data if d["model_name"] == model_name] 
        if user is not None and user != '':
            data = [d for d in data if d["user"] == user]
        if application is not None and application != '':
            data = [d for d in data if application in d["application"]]

        models = []
        for dict in data:
            models.append(dict["user"]+ '/' + dict["model_name"] + '/'+dict["version"])
        options = [{"label": entry, "value": entry} for entry in models]
        
        return options
    else:
        return []


@app.callback(
        [
            Output('model-gui', 'children'),
        ],
        [
            Input('search-dropdown', 'value'),
        ]
        )
def return_model_gui(dropdown_value):
    if dropdown_value is not None:
        data = model_list_GET_call()
        keys = ["user", "model_name", "version"]
        vals = dropdown_value.split('/') #user, model_name, versioin = vals[0], vals[1], vals[2]
        for key,val in zip(keys,vals):
            data = [d for d in data if d[key] == val]
        
        print(f'data0: {data[0]["gui_parameters"]}')
        
        item_list = JSONParameterEditor( _id={'type': 'parameter_editor'},
                                         json_blob=data[0]["gui_parameters"],           
                                        )
        item_list.init_callbacks(app)
        return [item_list]
    else:
        return [""]



# Setting up initial webpage layout
app.layout = html.Div (
        [
            header,
            dbc.Container(
                [
                    dbc.Row([dbc.Col(card1, width=6), dbc.Col(card2, width=6)]),
                    dbc.Row([dbc.Col(card3, width=10)]),
                ]
            ),
])



    
print("service registry is up running!")


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8052, debug=True)