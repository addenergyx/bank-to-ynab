# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 22:26:56 2020

@author: david
"""

# from server import server
# from tracker import app as tracker
# from mapout import app as mapout
# if __name__ == '__main__':
#     server.run()

## USE IN DEV/LOCAL ONLY

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from server import server as flask_app

from finances import app as app1
#from mapout import app as app2

application = DispatcherMiddleware(flask_app, {
    '/app1': app1.server,
#   '/app2': app2.server,
})

if __name__ == '__main__':
    run_simple('localhost', 8050, application)