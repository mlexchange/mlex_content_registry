# #!/usr/bin/env Python3
import io
import re

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, MATCH, ALL

import pymongo
import uuid
import json
import base64
import requests

from utility import conn_mongodb, get_content_list, get_dropdown_options, get_schema, validate_json, \
                    is_duplicate, update_mongodb, remove_key_from_dict_list, get_content
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


@app.callback(
    Output("collapse-app-port", "is_open"),
    Input("app-type", "value")
)
def toggle_app_port_inputform(app_type):
    if app_type == 'frontend':
        return True
    else:
        return False


# might need collapse to handle id not found issues
@app.callback( 
    Output("tab-display", "children"),
    Output("button-refresh", "children"),
    Output("collapse-model-tab", "is_open"),
    Output("collapse-app-tab", "is_open"),
    Output("collapse-workflow-tab", "is_open"),
    Output("table-model-list", "columns"),
    Input("tab-group","value")
    )
def update_layout(tab_value):
    if tab_value == 'model':
        return dash_forms('model'), 'Refresh Model List', True, False, False, [{'id': p, 'name': p} for p in MODEL_KEYS]
    elif tab_value == 'app':
        return dash_forms('app'), 'Refresh App List', False, True, False, [{'id': p, 'name': p} for p in APP_KEYS]
    elif tab_value == 'workflow':
        return dash_forms('workflow'), 'Refresh Workflow List', False, False, True, [{'id': p, 'name': p} for p in WORKFLOW_KEYS]
#     elif tab_value == 'resource':
#         return dash_forms('model'), 'Refresh Resources List', False, False, False, []


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
    Output('workflow-gui-container', 'children'),
    Input('workflow-group-add', 'n_clicks'),
    State('workflow-gui-container', 'children'))
def display_component(n_clicks, children):
    new_element = html.Div([
        dbc.Label("Choose a content by type:"),
        html.Div([
            dcc.Dropdown(
                id={
                    'type': 'content-type-dropdown',
                    'index': n_clicks
                },
                options=[{'label': i, 'value': i} for i in ['models', 'apps', 'workflows']],
                style={'width':'80%'},
                value='workflows',
            ),
            dcc.Dropdown(
                id={
                    'type': 'content-dropdown',
                    'index': n_clicks
                },
                options=get_dropdown_options('workflows'),
                style={'width':'100%'},
            ),
        ],
        style = {'width': '100%', 'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'},
        ),
        html.Div(
            id={
                'type': 'workflow-dynamic-output',
                'index': n_clicks
            }
        )
    ])
    children.append(new_element)
    return children


@app.callback(
    Output({'type': 'content-dropdown', 'index': MATCH}, 'options'),
    Input({'type': 'content-type-dropdown', 'index': MATCH}, 'value')
)
def options_for_workflow_dropdown(value):
    return get_dropdown_options(value)


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
    Input("access-type", "value"),
    Input("app-type", "value"),
    Input("app-cpu-num", "value"),
    Input("app-gpu-num", "value"),
    Input("model-cpu-num", "value"),
    Input("model-gpu-num", "value"),
    Input("cmd-regist", "value"),
    Input("workflow-execution-type", "value"),
    Input("workflow-gui-container", "children"),
    Input("dynamic-gui-container", "children"),
    Input("generate-json", "n_clicks"),
    Input("gui-check", "n_clicks"),
    Input('upload-data', 'contents'),
    State('app-port', 'value'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),

    prevent_initial_call=True
    )
def json_generator(content_type, component_type, name, version, model_type, uri, reference, \
                   description, applications, access_type, service_type, app_cpu_num, \
                   app_gpu_num, model_cpu_num, model_gpu_num, cmds, workflow_type, \
                   workflow_children, children, n1, n2, upload_content, ports, file_name, file_date):
    
    
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
        keys = ["name","version","type","uri","reference", "description", "public", "service_type"]
        items = [name, version, model_type, uri, reference, description, access_type, service_type]
        for item,key in zip(items,keys):
            if key in json_document and bool(item):
                json_document[key] = item

        if bool(applications):
            applications = applications.split(",")
            for application in applications:
                if application not in json_document["application"]:
                    json_document["application"].append(application)
        
        if "compute_resources" in json_document:
            if content_type == 'model':
                json_document["compute_resources"] = {"num_processors": model_cpu_num,
                                                      "num_gpus": model_gpu_num}
            else:
                json_document["compute_resources"] = {"num_processors": app_cpu_num,
                                                      "num_gpus": app_gpu_num}
        
        if "cmd" in json_document and bool(cmds):
            cmds = cmds.split(",")
            for cmd in cmds:
                if cmd not in json_document["cmd"]:
                    json_document["cmd"].append(cmd)
        
        if content_type == 'model':
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

                    if component_combo["type"] == "int" and "value" in component_combo:
                        component_combo["value"] = int(component_combo["value"])
                    elif component_combo["type"] == "float" and "value" in component_combo:
                        component_combo["value"] = float(component_combo["value"])
                    elif component_combo["type"] == "bool" and "value" in component_combo:
                        if component_combo["value"].lower() == 'true':
                            component_combo["value"] = True
                        else:
                            component_combo["value"] = False

                    json_document["gui_parameters"].append(component_combo)
            else:
                print('No gui component is added!')

        if content_type == 'workflow':
            if bool(workflow_type):
                json_document["workflow_type"] = workflow_type
            
            workflow_list = []
            if workflow_children is not None:
                for child in workflow_children:
                    workflow_list.append(child['props']['children'][1]['props']['children'][1]['props']['value'])
                json_document["workflow_list"] = workflow_list
                
        if content_type == 'app':
            if json_document["service_type"] == 'frontend' and bool(ports):
                json_document["map"] = {}
                ports = ports.split(",")
                for port in ports:
                    if port not in json_document["map"].keys():
                        json_document["map"][port] = ""
            
    if 'upload-data' in changed_id:
        json_document = {}
        if upload_content is not None:
            json_document = json.loads(base64.b64decode(upload_content.split(",")[1]))
            json_document["_id"] = str(uuid.uuid4()) 
            json_document["content_id"] = str(uuid.uuid4())
            json_document["owner"] = OWNER
            if "public" not in json_document:
                json_document["public"] = False
            
            if "content_type" in json_document:
                if json_document["content_type"] == "model":
                    if "service_type" not in json_document:
                        json_document["service_type"] = "backend"
    
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


#---------------------------------- launch jobs ------------------------------------------
def job_content_dict(content):
    job_content = {'mlex_app': content['name'],
                   'service_type': content['service_type'],
                   'working_directory': '',
                   'job_kwargs': {'uri': content['uri'], 
                                  'cmd': content['cmd'][0]}
    }
    if 'map' in content:
        job_content['job_kwargs']['map'] = content['map']
    
    return job_content


@app.callback(
    Output("workflow-ids", "data"),
    Output("job-type", "data"),
    Input("button-launch", "n_clicks"),
    State('table-model-list', 'selected_rows'),
    State("table-contents-cache", "data"),
    State("tab-group","value"),
    prevent_initial_call=True,
)
def launch_jobs(n_clicks, rows, data, tab_value):
    web_url = ''
    compute_dict = {'user_uid': '001',
                    'host_list': ['mlsandbox.als.lbl.gov', 'local.als.lbl.gov', 'vaughan.als.lbl.gov'],
                    'requirements': {'num_processors': 2,
                                     'num_gpus': 0,
                                     'num_nodes': 2},
                    }
    workflow_ids = []
    if tab_value == 'workflow':
        for row in rows:
            job_list = []
            dependency = {}
            workflow_list = data[row]['workflow_list']
            for i,job_id in enumerate(workflow_list):
                job_list.append(job_content_dict(get_content(job_id)))
                dependency[str(i)] = []
                if data[row]['workflow_type'] == 'serial':
                    for j in range(i):
                        dependency[str(i)].append(j) 

            compute_dict['job_list'] = job_list
            compute_dict['dependencies'] = dependency
            compute_dict['description'] = data[row]['name']+' v'+data[row]['version']
            if len(job_list)==1:
                compute_dict['requirements']['num_nodes'] = 1
            response = requests.post('http://job-service:8080/api/v0/workflows', json=compute_dict)
            workflow_ids.append(response.json())
    
    elif tab_value == 'model' or tab_value == 'app':
        job_list = []
        dependency = {}
        job_names = ''
        for i,row in enumerate(rows):
            job_content = job_content_dict(data[row])
            job_list.append(job_content) 
            dependency[str(i)] = []  #all modes and apps are regarded as independent at this time
            job_names += job_content['mlex_app'] + ', '
        
        compute_dict['job_list'] = job_list
        compute_dict['dependencies'] = dependency
        compute_dict['description'] = 'parallel workflow: ' + job_names
        if len(job_list)==1:
            compute_dict['requirements']['num_nodes'] = 1
        response = requests.post('http://job-service:8080/api/v0/workflows', json=compute_dict)
        workflow_ids.append(response.json())
        
    return workflow_ids, tab_value


@app.callback(
    Output("web-url", "data"),
    Input("button-open-window", "n_clicks"),
    State("workflow-ids", "data"),
)
def update_web_url(n_clicks, uids):
    web_url = ''
    if bool(uids): 
        uid = uids[0]
        port_url = 'http://job-service:8080/api/v0/workflows/{}/mapping'.format(uid)
        print(f'port_url {port_url}')
        response = requests.get(port_url).json()
        print(f'response {response}')
        for key1 in response:
            value1 = response.get(key1)
            for key2 in value1:
                port = value1.get(key2)
                port=port[0]["HostPort"]
                print(f'port {port}')
                web_url = "http://localhost:{}".format(port)
    
    return web_url


app.clientside_callback(
    """
    function(web_url, job_type) {
        if (job_type == 'app'){
            window.open(web_url);
        }
        return '';
    }
    """,
    Output('dummy', 'data'),
    Input('web-url', 'data'),
    State('job-type', 'data')
)


@app.callback(
    Output("table-job-list", "data"),
    Input("button-refresh-jobs", "n_clicks"),
    Input("tab-group","value"),
    prevent_initial_call=True,
)
def jobs_table(n, tab_value):
    job_list = []
    if tab_value == 'workflow':
        #response = requests.get('http://job-service:8080/api/v0/workflows', params={'state':'running'}).json()
        response = requests.get('http://job-service:8080/api/v0/workflows').json()
        for i,job in enumerate(response):
            job_uid = job['uid']
            job['submission_time'] = job['timestamps']['submission_time']
            job['execution_time'] = job['timestamps']['execution_time']
            job['job_status'] = job['status']['state']
            job_list.append(job)
    
    elif tab_value == 'model' or tab_value == 'app':
        response_get = requests.get('http://job-service:8080/api/v0/jobs').json()
        for i,job in enumerate(response_get):
            job_uid = job['uid']
            job['submission_time'] = job['timestamps']['submission_time']
            job['execution_time'] = job['timestamps']['execution_time']
            job['job_status'] = job['status']['state']
            job['description'] = job['job_kwargs']['uri']
            job_list.append(job)

    return job_list


@app.callback(
    Output("dummy1", "data"),
    Input("button-terminate", "n_clicks"),
    Input("table-job-list", "data"),
    Input("tab-group","value"),
    State('table-job-list', 'selected_rows'),
    prevent_initial_call=True,
)
def terminate_jobs(n_clicks, jobs, tab_value, rows):
    if bool(rows):
        for row in rows:
            job_id = jobs[row]['uid']
            print(f'terminate uid {job_id}')
            if tab_value == 'workflow':
                response = requests.patch(f'http://job-service:8080/api/v0/workflows/{job_id}/terminate')
            elif tab_value == 'model' or tab_value == 'app':
                response = requests.patch(f'http://job-service:8080/api/v0/jobs/{job_id}/terminate')
    
    return ''


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051, debug=True)
    print("model registry is up running!")


