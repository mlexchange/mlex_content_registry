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
    
    