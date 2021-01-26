# -*- coding: utf-8 -*-
"""
Created on Thu May 21 21:35:31 2020

@author: david
"""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def Fab():
    #html.Button("html", className='fixed-btn fas fa-plus glow-on-hover'),
    fab = html.Div(
                [
                    dbc.Button([html.Span(className='fa fa-bars icon')], className='fixed-btn'),
                    html.Ul(
                        [
                            #html.Li(dbc.Button([html.Span(className='fa fa-cog icon')], id='open', className='fixed-btn')),
                            html.Li(dbc.NavLink(dbc.Button([html.Span(className='fa fa-wallet icon')], className='fixed-btn'), href='../finance/', external_link=True)),
                            html.Li(dbc.NavLink(dbc.Button([html.Span(className='fa fa-running icon')], className='fixed-btn'), href='../fitness/', external_link=True)),
                            html.Li(dbc.NavLink(dbc.Button([html.Span(className='fa fa-chart-line icon')], className='fixed-btn'), href='../investments/', external_link=True)),   
                            html.Li(dbc.NavLink(dbc.Button([html.Span(className='fab fa-github icon')], className='fixed-btn'), href='https://github.com/addenergyx/bank-to-ynab', external_link=True)),
                        ],className='fab-options')
                ], className='fab-container'
              ),
    return fab