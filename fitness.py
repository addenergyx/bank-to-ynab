# -*- coding: utf-8 -*-
"""
Created on Fri May  1 09:42:42 2020

@author: david
"""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_daq as daq
from dash.dependencies import Input, Output
import numpy as np

external_stylesheets =['https://codepen.io/IvanNieto/pen/bRPJyb.css', dbc.themes.BOOTSTRAP, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']

app = dash.Dash(external_stylesheets=external_stylesheets, 
                meta_tags=[
                    { 'name':'viewport','content':'width=device-width, initial-scale=1' },## Fixes media query not showing
                    {
                        'name': 'description',
                        'content': 'This dashboard is designed to monitor events, deaths, and recoveries reported by serveral sources such as WHO and Johns Hopkins University on the n-Cov (Coronavirus). This constantly searches repositories and reviews all countries case studies.'
                    },
                ] 
            )

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%css%}
        {%favicon%}
    </head>
    <body>
        <div></div>
        {%app_entry%}
        <footer> 
          {%config%} 
          {%scripts%} 
          {%renderer%}
        </footer>
    </body>
</html>
'''

app.title = 'Digital Dashboard - Finance'

colors = {
    'background': '#191A1A',
    'text': '#FFFFFF',
    'secondary':'#2B2B2B'
}

body = html.Div(
    [
       dbc.Row(
           [
               ## Side Panel
               dbc.Col(
                  [
                     html.Div([
                         html.H2("Coronavirus Timeline Dashboard",style={'text-align':'center', 'padding-bottom':'20px', 'padding-top':'40px'}),
                    ], style={'color': '#0275d8'}),
                    
                    html.Div([
                                                
                        # html.Div([
                        #     dcc.Slider(
                        #         id='time-frame',
                        #         min = getTimeScaleUnix()[0],
                        #         max = getTimeScaleUnix()[-1],
                        #         value = getTimeScaleUnix()[-1],
                        #         #updatemode='drag',
                        #         #tooltip = { 'always_visible': True },
                        #         marks=getMarks(12),
                        #         step=1,
                        #     ),
                        # ]),
                        
                        html.Div([
                            html.H3("Global Coronavirus News", style={'color': colors['text'], 'text-align':'center'}),
                        ],style={'padding-bottom':'20px','padding-top':'20px'}),
                        ], style={'padding-right':'20px','padding-left':'20px'}),
                    ], width=12,lg=3, className='card', style={'backgroundColor': colors['secondary'],'padding-top':'80px'} ),
              
              ## Main panel
              dbc.Col(
                  [
                      # dbc.Col([
                      #     html.Div([
                      #       daq.ToggleSwitch(
                      #           id='exclude-china',
                      #           value=True,
                      #           label=['Excluding China', 'Including China'],
                      #           color='#0275d8',
                      #           style={
                      #               'color': 'white'
                      #           }
                      #       ),
                      #    ]),
                      # ], width={"size": 2, "offset":9}),
                      dcc.Loading(
                          children=[
                              html.Div([
                                  dcc.Graph(
                                    id='corona-map',
                                    #figure=fig,
                                    style={'margin' : '0'},
                                  ),
                             ])
                         ], type='circle',
                      )
                  ],style={'padding-top':'80px'}, width=12, lg=9
            )
       ]),
       
  ])
    
def Homepage():
    layout = html.Div([
        body,
    ], style={'backgroundColor': colors['background'], 'overflow-x': 'hidden', 'height':'100%'})
    return layout

app.layout = Homepage()

if __name__ == "__main__":
    #app.run_server()
    app.run_server(debug=True, use_reloader=False)


























