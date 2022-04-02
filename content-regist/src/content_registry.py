# #!/usr/bin/env Python3

import io
import re

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, MATCH, ALL

import pymongo
import uuid
import json
import base64

from utility import conn_mongodb, get_content_list, get_schema, validate_json, is_duplicate, \
                    update_mongodb, remove_key_from_dict_list
from generator import make_form_input, make_form_slider, make_form_dropdown, make_form_radio, \
                      make_form_bool, make_form_graph

from targeted_callbacks import targeted_callback
from kwarg_editor import JSONParameterEditor

from app_layout import app, data_uploader, dash_forms, MODEL_TEMPLATE, APP_TEMPLATE, WORKFLOW_TEMPLATE, \
                       MODEL_KEYS, APP_KEYS, WORKFLOW_KEYS, OWNER

#----------------------------------- callback reactives ------------------------------------
@app.callback(
    Output("table-model-list", "data"),
    Input("table-contents-cache", "data"),  # automatically refresh table after delete, not after upload though
    Input("button-refresh", "n_clicks"),
    Input("tab-group","value"),
    )
def refresh_table(data, n_cliks, tab_value):
    model_list = get_content_list(tab_value+'s')
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-refresh' in changed_id:
        model_list = get_content_list(tab_value+'s')
    
    return model_list


@app.callback(
    Output("modal", "is_open"),
    Input("button-delete", "n_clicks"),
    Input("confirm-delete", "n_clicks"),  
    State("modal", "is_open")
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# might need collapse to handle id not found issues
@app.callback( 
    Output("tab-display", "children"),
    Output("button-refresh", "children"),
    Output("collapse-model-tab", "is_open"),
    Output("collapse-workflow-tab", "is_open"),
    Output("table-model-list", "columns"),
    Input("tab-group","value")
    )
def update_layout(tab_value):
    if tab_value == 'model':
        return dash_forms('model'), 'Refresh Model List', True, False, [{'id': p, 'name': p} for p in MODEL_KEYS]
    elif tab_value == 'app':
        return dash_forms('app'), 'Refresh App List', False, False, [{'id': p, 'name': p} for p in APP_KEYS]
    elif tab_value == 'workflow':
        return dash_forms('workflow'), 'Refresh Workflow List', False, True, [{'id': p, 'name': p} for p in WORKFLOW_KEYS]


@app.callback( 
    Output("table-contents-cache", "data"),
    Input('table-model-list', 'selected_rows'),
    Input('confirm-delete', 'n_clicks'),
    State("tab-group","value")
    )
def update_regist(rows, n_click, tab_value):
    content_list = get_content_list(tab_value+'s')
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'confirm-delete' in changed_id:
        if bool(rows):
            content_ids = [] 
            for row in rows:
                if 'content_id' in content_list[row]:
                    content_ids.append(content_list[row]['content_id'])

            for content_id in content_ids:
                mycollection = conn_mongodb(tab_value+'s') 
                mycollection.delete_one({"content_id": content_id})

    return get_content_list(tab_value+'s')


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
    Output("json-store", "data"),
    Output("data-uploader", "children"),
    Input("tab-group","value"),
    Input({'type': 'dynamic-dropdown', 'index': ALL}, 'value'),
    Input("name-regist", "value"),
    Input("version-regist", "value"),
    Input("model-type", "value"),
    Input("uri-regist", "value"),
    Input("reference-regist", "value"),
    Input("description-regist", "value"),
    Input("application-regist", "value"),
    Input("cmd-regist", "value"),
    Input("workflow-dependencies", "value"),
    Input("dynamic-gui-container", "children"),
    Input("generate-json", "n_clicks"),
    Input("gui-check", "n_clicks"),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),

    prevent_initial_call=True
    )
def json_generator(content_type, component_type, name, version, model_type, uri, \
                   reference, description, applications, cmds, dependencies, children, n1, n2, \
                   upload_content, file_name, file_date):
    
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    #print(f'gui container children\n{children}')
    
    json_document = MODEL_TEMPLATE.copy()  # shallow copy
    if content_type == 'model':
        json_document["gui_parameters"] = []  # set the gui parameter list to empty
    if content_type == 'app':
        json_document = APP_TEMPLATE.copy()
    elif content_type == 'workflow':
        json_document = WORKFLOW_TEMPLATE.copy()
        
    json_document["_id"] = str(uuid.uuid4())
    json_document["content_id"] = str(uuid.uuid4())
    
    if 'generate-json' in changed_id or \
       'gui-check' in changed_id:
        keys = ["name","version","type","uri","reference", "description"]
        items = [name, version, model_type, uri, reference, description]
        for item,key in zip(items,keys):
            if key in json_document and bool(item):
                json_document[key] = item

        if bool(applications):
            applications = applications.split(",")
            for application in applications:
                if application not in json_document["application"]:
                    json_document["application"].append(application)
        
        if 'cmd' in json_document and bool(cmds):
            cmds = cmds.split(",")
            for cmd in cmds:
                if cmd not in json_document["cmd"]:
                    json_document["cmd"].append(cmd)
                    
        if "dependency" in json_document and bool(dependencies):
            workflow_dependencies = []
            apps = dependencies.split(',')
            for app in apps:
                parallel_apps = app.split(';')
                if len(parallel_apps) == 1:
                    workflow_dependencies.append(app)
                else:
                    para_apps = []
                    for item in parallel_apps:
                        para_apps.append(item)
                    workflow_dependencies.append(para_apps)
            json_document['dependency'] = workflow_dependencies
        
        if children[0]['props']['children'][2]['props']['children'] is not None and bool(component_type):
            for k,child in enumerate(children):
                input_items = child['props']['children'][2]['props']['children']['props']['children'][1]['props']['children']
                length = len(input_items)
                component_combo = {"type":component_type[k]}
                for input_item in input_items:
                    if 'value' in input_item['props']:
                        input_type  = input_item["props"]["id"]["subtype"]
                        input_value = input_item["props"]["value"]
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
            if json_document['content_type'] == 'model':
                print('No gui component is added!')

    if 'upload-data' in changed_id:
        json_document = {}
        if upload_content is not None:
            json_document = json.loads(base64.b64decode(upload_content.split(",")[1]))
            json_document["_id"] = str(uuid.uuid4()) 
            json_document["content_id"] = str(uuid.uuid4())
            json_document["owner"] = OWNER
    
    return json_document, data_uploader


@app.callback(
    Output("nothing", "data"),
    Input('button-register', 'n_clicks'),
    Input('button-upload', 'n_clicks'),
    State('validation', 'data'),
    State("json-store", "data")
)
def add_new_content(n1, n2, is_valid, json_document):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-upload.n_clicks' in changed_id:
        if bool(json_document) and is_valid:
            mycollection = conn_mongodb(json_document['content_type']+'s')
            mycollection.insert_one(json_document)

    if 'button-register.n_clicks' in changed_id:
        if bool(json_document):
            mycollection = conn_mongodb(json_document['content_type']+'s')
            mycollection.insert_one(json_document)


@app.callback(
    Output('output-json-validation', 'children'),
    Output('validation', 'data'),
    Input("button-validate", "n_clicks"),
    State('json-store', 'data')
)
def validate_json_schema(n, data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-validate' in changed_id:
        if bool(data):
            is_valid, msg = validate_json(data, data['content_type'])
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
    data = dash.callback_context.states["json-store.data"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'gui-check' in changed_id and 'gui_parameters' in data:
        if bool(data["gui_parameters"]):
            item_list = JSONParameterEditor( _id={'type': 'parameter_editor'},   # pattern match _id (base id), name
                                             json_blob=remove_key_from_dict_list(data["gui_parameters"], "comp_group"),
                                            )
            item_list.init_callbacks(app)
            return [html.H5("GUI Layout", className="card-title"), item_list]
        else:
            return[""]
    else:
        return [""]

targeted_callback(
    show_dynamic_gui_layouts,
    Input("gui-check", "n_clicks"),
    Output("gui-layout", "children"),
    State("json-store", "data"),
    app=app)


def show_gui_layouts(n_clicks):
    data = dash.callback_context.states["json-store.data"]
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'button-validate' in changed_id and 'gui_parameters' in data:
        if bool(data["gui_parameters"]):
            is_valid, msg = validate_json(data, data['content_type'])
            if is_valid:
                item_list = JSONParameterEditor(_id={'type': 'parameter_editor'},   # pattern match _id (base id), name
                                                json_blob=remove_key_from_dict_list(data["gui_parameters"], "comp_group"),
                                            )
                item_list.init_callbacks(app)
                return [html.H5("GUI Layout", className="card-title"), item_list]
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
    State("json-store", "data"),
    prevent_initial_call=True,
)
def download_model(n_clicks, data):
    filename = data["name"] + "_v" + data["version"]
    return dict(content=json.dumps(data), filename="{}.json".format(filename))



if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051, debug=True)
    print("model registry is up running!")



