# #!/usr/bin/env Python3
import io
import re

from dash import html, dcc, Input, Output, State, MATCH, ALL, ctx
import dash_bootstrap_components as dbc

import pymongo
import uuid
import json
import base64
import requests

from registry_util import conn_mongodb, get_content_list, get_dash_table_data, filter_dash_table_data, \
                    get_dropdown_options, get_schema, validate_json, is_duplicate, update_mongodb, \
                    remove_key_from_dict_list, get_content, job_content_dict, send_webhook
from form_generator import make_form_input, make_form_slider, make_form_dropdown, make_form_radio, \
                      make_form_bool, make_form_img, make_form_graph

from dash_component_editor import JSONParameterEditor

from app_layout import app, data_uploader, dash_forms, ContentVariables


#----------------------------------- callback reactives ------------------------------------
@app.callback(
    Output("table-model-list", "data"),
    Input("table-contents-memo", "data"),  # automatically refresh table after delete, not after upload though; mlex_userhome need it.
    Input("tab-group", "value"),
    Input("monitoring", "n_intervals")
    )
def refresh_table(data, tab_value, n_intervals):
    model_list = get_dash_table_data(collection=tab_value+'s', fields={key:1 for key in ContentVariables.MODEL_KEYS})
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


@app.callback(
    Output("collapse-open-app", "is_open"),
    Input("tab-group","value"),
)
def toggle_open_app_button(tab_group):
    if tab_group == 'workflow':
        return False
    else:
        return True


# might need collapse to handle id not found issues
@app.callback( 
    Output("tab-display", "children"),
    Output("collapse-model-tab", "is_open"),
    Output("collapse-app-tab", "is_open"),
    Output("collapse-workflow-tab", "is_open"),
    Output("table-model-list", "columns"),
    Input("tab-group","value")
    )
def update_layout(tab_value):
    if tab_value == 'model':
        return dash_forms('model'), True, False, False, [{'id': p, 'name': p} for p in ContentVariables.MODEL_KEYS]
    elif tab_value == 'app':
        return dash_forms('app'), False, True, False, [{'id': p, 'name': p} for p in ContentVariables.APP_KEYS]
    elif tab_value == 'workflow':
        return dash_forms('workflow'), False, False, True, [{'id': p, 'name': p} for p in ContentVariables.WORKFLOW_KEYS]


@app.callback( 
    Output("table-contents-memo", "data"),
    Input('table-model-list', 'selected_rows'),
    Input('confirm-delete', 'n_clicks'),
    State("tab-group","value")
    )
def delete_content(rows, n_click, tab_value):
    content_list = get_content_list(tab_value+'s')
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if 'confirm-delete' in changed_id:
        if rows:
            content_ids = [] 
            for row in rows:
                if 'content_id' in content_list[row]:
                    content_ids.append(content_list[row]['content_id'])

            for content_id in content_ids:
                mycollection = conn_mongodb(tab_value+'s') 
                mycollection.delete_one({"content_id": content_id})
                send_webhook({"event": "delete_content", "content_id": content_id, "content_type": tab_value})

    return get_content_list(tab_value+'s')


comp_labels = ['input form (int)', 'input form (float)', 'input form (str)', 'slider','dropdown','radio items','boolean toggle switch','image'] #'graph uploader' (deprecated)
comp_values = ['int', 'float', 'str', 'slider', 'dropdown', 'radio', 'bool', 'img'] #'graph'
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
            options=[{'label': l, 'value': v} for l, v in zip(comp_labels,comp_values)]
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
    i = int(re.findall('(?<="index":)\\d+(?=,)', ctx.triggered[0]['prop_id'])[0])
    if value in ['int','float','str']:
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_input(i)])
    elif value == 'dropdown':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_dropdown(i)])
    elif value == 'slider':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_slider(i)])
    elif value == 'radio':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_radio(i)])
    elif value == 'bool':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_bool(i)])
    elif value == 'img':
        return dbc.Card([dbc.Label("GUI paramerers for {} component".format(value), className="mr-2"), make_form_img(i)])
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
    Input("kwargs-regist", "value"),
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
                   app_gpu_num, model_cpu_num, model_gpu_num, cmds, kwargs, workflow_type, \
                   workflow_children, children, n1, n2, upload_content, ports, file_name, file_date):
    
    
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    #print(f'gui container children\n{children}')
    
    json_document = ContentVariables.MODEL_TEMPLATE.copy()  # shallow copy
    if content_type == 'model':
        json_document["gui_parameters"] = []  # set the gui parameter list to empty
    if content_type == 'app':
        json_document = ContentVariables.APP_TEMPLATE.copy()
    elif content_type == 'workflow':
        json_document = ContentVariables.WORKFLOW_TEMPLATE.copy()
        
    json_document["_id"] = str(uuid.uuid4())
    json_document["content_id"] = str(uuid.uuid4())
    
    if 'generate-json' in changed_id or \
       'gui-check' in changed_id:
        keys = ["name","version","type","uri","reference", "description", "public", "service_type"]
        items = [name, version, model_type, uri, reference, description, access_type, service_type]
        for item,key in zip(items,keys):
            if key in json_document and item:
                json_document[key] = item

        if applications:
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
        
        if "cmd" in json_document and cmds:
            cmds = cmds.split(",")
            for cmd in cmds:
                if cmd not in json_document["cmd"]:
                    json_document["cmd"].append(cmd)
        
        if "kwargs" in json_document and kwargs:
            kwargs =  json.loads(str(kwargs))
            json_document["container_kwargs"]=kwargs
            
        if content_type == 'model':
            if children[0]['props']['children'][2]['props']['children'] is not None and component_type:
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
#                         else:
#                             print('No value is found in the input form yet')

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
            if workflow_type:
                json_document["workflow_type"] = workflow_type
            
            workflow_list = []
            if workflow_children is not None:
                for child in workflow_children:
                    workflow_list.append(child['props']['children'][1]['props']['children'][1]['props']['value'])
                json_document["workflow_list"] = workflow_list
                
        if content_type == 'app':
            if json_document["service_type"] == 'frontend' and ports:
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
            json_document["owner"] = ContentVariables.OWNER
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
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if 'button-upload.n_clicks' in changed_id:
        if json_document and is_valid:
            mycollection = conn_mongodb(json_document['content_type']+'s')
            mycollection.insert_one(json_document)
            send_webhook({"event": "add_content", "content_id": json_document["content_id"], "content_type": json_document["content_type"]})

    if 'button-register.n_clicks' in changed_id:
        if json_document:
            mycollection = conn_mongodb(json_document['content_type']+'s')
            mycollection.insert_one(json_document)
            msg = {'event': 'add_content', 'content_id': json_document['content_id']}
            print(f'Producer: sending webhook msg {msg}')
            send_webhook({"event": "add_content", "content_id": json_document["content_id"], "content_type": json_document["content_type"]})


@app.callback(
    Output('output-json-validation', 'children'),
    Output('validation', 'data'),
    Input("button-validate", "n_clicks"),
    State('json-store', 'data')
)
def validate_json_schema(n, data):
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if 'button-validate' in changed_id:
        if data:
            is_valid, msg = validate_json(data, data['content_type'])
            return [str(msg),is_valid]
        else:
            return ["", False]
    else:
        return ["", False]


@app.callback(
    Output("download-text", "data"),
    Input("btn-download-txt", "n_clicks"),
    State("json-store", "data"),
    prevent_initial_call=True,
)
def download_model(n_clicks, data):
    filename = data["name"] + "_v" + data["version"]
    return dict(content=json.dumps(data), filename="{}.json".format(filename))


#--------------------------- Duplicated callbacks to update GUI components (demonstration)--------------------
@app.callback(
    Output("gui-layout", "children", allow_duplicate=True),
    Input("gui-check", "n_clicks"),
    State("json-store", "data"),
    prevent_initial_call=True
)
def show_gui_layouts(n_clicks, data):
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if 'gui-check' in changed_id and 'gui_parameters' in data:
        if data["gui_parameters"]:                    
            item_list = JSONParameterEditor( _id={'type': 'parameter_editor'},   # pattern match _id (base id), name
                                             json_blob=remove_key_from_dict_list(data["gui_parameters"], "comp_group"),
                                            )
            item_list.init_callbacks(app)
            return [html.H5("GUI Layout", className="card-title"), item_list]
        else:
            return[""]
    else:
        return [""]
        

@app.callback(
    Output("gui-layout", "children", allow_duplicate=True),
    Input("button-validate", "n_clicks"),
    State("json-store", "data"),
    prevent_initial_call=True
)
def show_gui_layouts(n_clicks, data):
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if 'button-validate' in changed_id and 'gui_parameters' in data:
        if data["gui_parameters"]:
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

#---------------------------------- launch jobs ------------------------------------------
@app.callback(
    Output("dummy", "data"),
    Input("button-launch", "n_clicks"),
    Input("terminate-user-jobs", "n_clicks"),
    #State("table-model-list", "data"),
    State("table-contents-memo", "data"),
    State('table-model-list', 'selected_rows'),
    State("table-job-memo", "data"),
    State('table-job-list', 'selected_rows'),
    State("tab-group","value"),
    prevent_initial_call=True,
)
def apps_jobs(n_clicks, n_terminate, data, rows, job_data, job_rows, tab_value):
    user_id = '001'
    changed_id = [p['prop_id'] for p in ctx.triggered][0]
    if "button-launch.n_clicks" in changed_id:
        job_request = {'user_uid': user_id,
                       'host_list': ['mlsandbox.als.lbl.gov', 'local.als.lbl.gov', 'vaughan.als.lbl.gov'],
                       'requirements': {'num_processors': 2,
                                        'num_gpus': 0,
                                        'num_nodes': 2},
                      }
                    
        job_list = []
        dependency = {}
        job_names = ''
        if tab_value == 'workflow':
            if rows:
                for row in rows:
                    job_list = []
                    dependency = {}
                    print(f'data[row] {data[row]}')
                    if 'workflow_list' in data[row]:
                        workflow_list = data[row]['workflow_list']
                        for i,job_id in enumerate(workflow_list):
                            job_list.append(job_content_dict(get_content(job_id), user_id))
                            print(f'job_list {job_list}')
                            dependency[str(i)] = []
                            if data[row]['workflow_type'] == 'serial':
                                for j in range(i):
                                    dependency[str(i)].append(j) 

                    job_request['job_list'] = job_list
                    job_request['dependencies'] = dependency
                    job_request['description'] = data[row]['name']+' v'+data[row]['version']
                    if len(job_list)==1:
                        job_request['requirements']['num_nodes'] = 1
                    response = requests.post('http://job-service:8080/api/v0/workflows', json=job_request)
                    print(f'workflow response {response}')
        
        elif tab_value == 'model' or tab_value == 'app':
            if rows:
                for i,row in enumerate(rows):
                    job_content = job_content_dict(data[row], user_id)
                    job_list.append(job_content) 
                    dependency[str(i)] = []  #all modes and apps are regarded as independent at this time
                    job_names += job_content['mlex_app'] + ', '
    
            job_request['job_list'] = job_list
            job_request['dependencies'] = dependency
            job_request['description'] = 'parallel workflow: ' + job_names
            if len(job_list) == 1:
                job_request['requirements']['num_nodes'] = 1
            response = requests.post('http://job-service:8080/api/v0/workflows', json=job_request)
            print(f'model/app response {response}')
    
    if "terminate-user-jobs.n_clicks" in changed_id:
        print('Terminating jobs')
        if job_rows:
            for job_row in job_rows:
                job_id = job_data[job_row]['uid']
                print(f'terminate uid {job_id}')
                if tab_value == 'workflow':
                    response = requests.patch(f'http://job-service:8080/api/v0/workflows/{job_id}/terminate')
                elif tab_value == 'model' or tab_value == 'app':
                    response = requests.patch(f'http://job-service:8080/api/v0/jobs/{job_id}/terminate')

    return ''


@app.callback(
    Output("table-job-list", "data"),
    Output("table-job-memo", "data"),
    Input("tab-group","value"),
    Input("monitoring", "n_intervals"),
    prevent_initial_call=True,
)
def jobs_table(tab_value, n_interval):
    user_id = '001'
    job_list = []
    if tab_value == 'workflow':
        #response = requests.get('http://job-service:8080/api/v0/workflows', params={'state':'running'}).json()
        #response = requests.get('http://job-service:8080/api/v0/workflows?user={user_id}').json()
        response = requests.get('http://job-service:8080/api/v0/workflows').json()
    elif tab_value == 'model' or tab_value == 'app':
        response = requests.get('http://job-service:8080/api/v0/jobs').json()

    for i,job in enumerate(response):
        job_uid = job['uid']
        job['submission_time'] = job['timestamps']['submission_time']
        job['execution_time'] = job['timestamps']['execution_time']
        job['job_status'] = job['status']['state']
        if tab_value == 'model' or tab_value == 'app':
            job['description'] = job['job_kwargs']['uri']
        job_list.append(job)

    return filter_dash_table_data(job_list[::-1], ContentVariables.JOB_KEYS), job_list[::-1]


@app.callback(
    Output("web-urls", "data"),
    Input("button-open-window", "n_clicks"),
    State("table-job-memo", "data"),
    State('table-job-list', 'selected_rows'),
    prevent_initial_call=True,
)
def update_app_url(n_clicks, jobs, rows):
    web_urls = []
    if rows:
        for row in rows:
            if jobs[row]['service_type'] == 'frontend' and 'map' in jobs[row]['job_kwargs']:
                mapping = jobs[row]['job_kwargs']['map']
                for key in mapping:
                    port = mapping.get(key)
                    if port:
                        port=port[0]["HostPort"]
                        web_url = "http://localhost:{}".format(port)
                        web_urls.append(web_url)
    
    return web_urls


app.clientside_callback(
    """
    function(web_urls) {
        for (let i = 0; i < web_urls.length; i++) { 
            window.open(web_urls[i]);
        }
        return '';
    }
    """,
    Output('dummy1', 'data'),
    Input('web-urls', 'data'),
)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8051, debug=True)
    print("model registry is up running!")


