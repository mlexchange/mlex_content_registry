import dash_bootstrap_components as dbc


group_label = dbc.Label("Group key for this component, e.g., training or testing (optional, default key value is all).")
#===================================== dynamic JSON generator ============================
def make_form_input(i):
    form_input = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="text", placeholder="default value (optional)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_input

def make_form_slider(i):
    form_slider = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "min"},   type="number", placeholder="min"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "max"},   type="number", placeholder="max"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "step"},  type="number", placeholder="step"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="number", placeholder="default value (optional)"),
            dbc.Label("Input marks following: value1, label1, value2, label2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "marks"}, type="text", placeholder="marks (optional, default is None)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_slider


def make_form_dropdown(i):    
    form_dropdown = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},   type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"},  type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},    type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"},  type="text", placeholder="default value (optional)"),
            dbc.Label("Input options following: label1, value1, label2, value2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "options"},type="text", placeholder="options"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_dropdown


def make_form_radio(i):
    form_radio = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},    type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"},   type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},     type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"},   type="text", placeholder="default value (optional)"),
            dbc.Label("Input options following: label1, value1, label2, value2..."),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "options"}, type="text", placeholder="options (required)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_radio


def make_form_bool(i):
    form_bool = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"},   type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "value"}, type="text", placeholder="default value (optional, default is False)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_bool


def make_form_img(i):
    form_img = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "src"}, type="text", placeholder="image src (required, full docker path)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"}, type="text", placeholder="parameter key used in cmd (default is component id)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "width"}, type="text", placeholder="image width, e.g., 50%, 30 or 30px (optional, default is 100px)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_img


def make_form_graph(i):
    form_graph = dbc.Form(
        [
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "name"},  type="text", placeholder="component id (unique for each component)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "title"}, type="text", placeholder="title (optional)"),
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "param_key"}, type="text", placeholder="parameter key used in cmd (default is component id)"),
            group_label,
            dbc.Input(id={"type": "dynamic-component", "index": i, "subtype": "comp_group"}, type="text", value = 'all', placeholder="group key (optional, default is all)")
        ])
    return form_graph
    
    