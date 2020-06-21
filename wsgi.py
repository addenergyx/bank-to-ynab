# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 21:41:12 2020

@author: david
"""
import datetime
from dash import Dash
from werkzeug.middleware.dispatcher import DispatcherMiddleware

from finances import app as app1
#from mapout import app as app2
from server import server as flask_app
from dotenv import load_dotenv

# Load env vars
load_dotenv(verbose=True, override=True)

application = DispatcherMiddleware(flask_app, {
    '/app1': app1.server,
#    '/app2': app2.server,
})  