# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 07:02:46 2020

@author: david
"""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_daq as daq
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from dash_extensions.callback import DashCallbackBlueprint
import plotly.express as px
from random import randint
import dash_table
from visuals import performance_chart, ml_model, period_chart, goal_chart, profit_loss_chart, cumsum_chart, dividend_chart
from components import Fab
from server import server
import os
from sqlalchemy import create_engine

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

external_stylesheets =['https://codepen.io/IvanNieto/pen/bRPJyb.css', dbc.themes.BOOTSTRAP, 
                       'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.0/css/all.min.css']

app = dash.Dash(__name__, server=server, url_base_pathname='/investments/', external_stylesheets=external_stylesheets, assets_folder='./assets/investment_assets',
                meta_tags=[
                    { 'name':'viewport','content':'width=device-width, initial-scale=1, shrink-to-fit=no' }, ## Fixes media query not showing
                    {
                        'name':'description',
                        'content':'Investments',
                    },
                    {
                        'name':'keywords',
                        'content':'Investments',
                    },                        

                    {
                        'property':'og:image',
                        'content':'',
                    },
                    {
                        'name':'title',
                        'content':'Investments',                    
                    }
                ]
            )

#server = app.server

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

portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day'])

app.title = 'Investments'

colours = {
            'remaining':'#1FDBB5',
            'principal':'#F54784',
            'interest':'#FFAC51'
          }

graph_card = [
                html.Div([            
                    dcc.Loading(
                        dcc.Graph(id='graphy'#, figure=performance_chart('TSLA')
                                  )
                    )
                ], id='graph-block', hidden=False)
             ]

profit_card = [
                html.Div([            
                    dcc.Loading(
                        dcc.Graph(id='profit-graph')
                    )
                ], id='profit-block', hidden=False)
             ]

stats_card = [
                dbc.CardBody(
                    [
                        html.H2('Results'),
                        html.P("This Month's Opening Balance"),
                        html.Strong(html.P(id='monthly-repayment', className='result')),
                        html.P("This Month's Realised P/L"),
                        html.Strong(html.P(id='monthly-profit', className='result')),
                        html.P('Total Realised P/L'),
                        html.Strong(html.P(id='total-repayable', className='result')),
                        # html.P('Floating P/L'),
                        # html.Strong(html.P(id='total-interest', className='result'))
                    ], className='stats'
                )
             ]

# Returns Top cell bar for header area
# def get_top_bar_cell(cellTitle, cellValue):
#     return html.Div(
#         #className="two-col",
#         children=[
#             html.P(className="p-top-bar", children=cellTitle),
#             html.P(id=cellTitle, className="display-none", children=cellValue),
#             html.P(children=human_format(cellValue)),
#         ],
#     )


# def rows(row, df):
#     pp = []
#     for x in range(0, len(df.columns)):
#         pp.append(html.Td(
#             html.P(row.values[x], className='balances'), **{'data-label': 'Month'}
#         ))
#     return pp
        
# def build_table(df):
#     return html.Div(
#     [
#         #Header
#         html.Table([html.Tr([html.Th(col) for col in df.columns])]
#         +
#         #body
#         [
#             html.Tr(
#                 [
#                     rows(row, df)
  
#                 ]) for i, row in df.iterrows()], className="hover-table amortization-table"
#         ), 
#     ], className='table-block', #style={"height": "100%", "overflowY": "scroll", "overflowX": "hidden"}, #className='large-2'
#     )

def build_table(df):
    return html.Div(
    [
        #Header
        html.Table([html.Tr([html.Th(col) for col in df.columns[:7]])]
        +
        #body
        [
            html.Tr(
                [
                    html.Td(
                        html.P(row.values[0], className='balances'), **{'data-label': 'Month'}
                    ),
                    html.Td(
                        html.P(row.values[1], className='balances'), **{'data-label': 'Payment'} 
                    ),
                    html.Td(
                        html.P(row.values[2], className='balances'), className='amount', **{'data-label': 'Principal'}
                    ),
                    html.Td(
                        html.P((row.values[3]), className='balances'), className='amount', **{'data-label': 'Interest'}
                    ),
                    html.Td(
                        html.P((row.values[4]), className='balances'), className='amount', **{'data-label': 'Total Interest'} 
                    ),
                    html.Td(
                        html.P((row.values[5].strftime("%d/%m/%Y")), className='balances'), className='amount', **{'data-label': 'Balance'} 
                    ),
                ]) for i, row in df.iterrows()], className="hover-table amortization-table"
        ), 
    ], className='table-block', #style={"height": "100%", "overflowY": "scroll", "overflowX": "hidden"}, #className='large-2'
    )

def build_card(title, colour):
    return html.Div(
        [
            dbc.Row(
                [
                    #dbc.Col(html.Span(className='fas fa-money-bill-wave icon', style={'color':colour}), className='d-flex justify-content-center icon-container', width=3), 
                    dbc.Col(
                        [
                            html.P(title.capitalize(), className='money')
                        ], className='d-flex justify-content-center text-center')
                ]
            ),
            dbc.Row(
                [
                    #dbc.Col(width=3),
                    dbc.Col(html.P(id=f'{title}-value'), className='d-flex justify-content-center text-center')
                ]
            ),
        ]
    )

app.config.suppress_callback_exceptions = True

tickers = [{'label':str(x), 'value': x} for x in set(portfolio['Ticker Symbol'])]
charts = [{'label':str(x), 'value': x} for x in ['Goals', 'Monthly', 'Dividends', 'Cumulative', 'Profit/Loss', 'Daily', 'Weekly', 'Quarterly', 'Fiscal Year']]

body = html.Div(
            [
              dbc.Row(
                    [
                        ## Side Panel
                        dbc.Col(
                           [
                               html.H1('Investments', style={'text-align':'center'}),
                              
                               html.Div(
                                   [
                                        html.Div(dbc.Row([ dbc.Col(dbc.Card(stats_card, className='summary-card stats-card',  ))]), hidden=False, id='statss' )
                                        
                                   ], id='user-inputs'
                               ),
                              
                              #html.Div(style={'margin':'200px'}),
                              
                             html.Div(
                                   [
                                  dcc.Dropdown(
                                    id='chart-dropdown',
                                    options=charts,
                                    value='Goals',
                                    clearable=False,
                                    style={'margin-top':'100px'}
                                  ),
                              ]),
                               
                              html.Div(
                                   [
                                  dcc.Dropdown(
                                    id='ticker-dropdown',
                                    options=tickers,
                                    value='TSLA',
                                    #clearable=False,
                                    searchable=True,
                                    style={'margin-top':'50px'}
                                  ),
                              ]),
                              
                           ], id='side-panel', width=12, lg=3
                        ),
                      
                       ## Main panel
                       dbc.Col(
                           [                      
                            
                            # dbc.Row(
                            #        [
                            #            # Top Bar Div - Displays Balance, Equity, ... , Open P/L
                            #            html.Div(
                            #                id="top_bar", className="row div-top-bar", children=get_top_bar()
                            #             ),
                            #        ], className = 'data-row'
                            #    ),
                                                               
                            #    html.Div([
                            #        dbc.Row(
                            #            [
                            #                dbc.Col(build_card('Open Balance', colours['remaining']), width=4),
                            #                dbc.Col(build_card('Realised P/L', colours['principal']), width=4),
                            #                dbc.Col(build_card('Floating P/L', colours['interest']), width=4),
    
                            #            ], className='data-row'
                            #        ),
                            #    ], id='stats-block'),
                               
                               dbc.Row(
                                   [
                                       dbc.Col(html.Div(profit_card), width=12),
                                   ], className = 'data-row'
                               ),
                               
                               dbc.Row(
                                   [
                                       dbc.Col(html.Div(graph_card), width=12),
                                   ], className = 'data-row'
                               ),
                               
                               dbc.Row(
                                   [
                                       dbc.Col(dbc.Card(id='full-data-card', className='summary-card'), width=12, lg=8),
                                       dbc.Col(dbc.Card( 
                                           # children=[                 
                                           #     dcc.Loading(
                                           #         dcc.Graph(id='ml-graph'#, figure=ml_model()
                                           #                   )
                                           #     )
                                           # ],
                                           #html.P(id='advice'), 
                                           #id='side-data-card', 
                                           className='summary-card justify-content-center align-self-center'), width=12, lg=4),
                                       # dbc.Col(dbc.Card(stats_card, id='side-data-card', className='summary-card'), width=12, lg=4),
                                       # #dbc.Col(dbc.Card(aaa, id='test', className='summary-card'), width=12, lg=4),
                                   ], className = 'data-row'
                               ),
                                                    
                               dbc.Row(
                                   [
                                       dbc.Col(width=12),
                                   ], className = 'data-row'
                               ),
                                                    
                               dcc.Interval(id="weight-interval", n_intervals=0, interval=600000),
                              
                           ], id='main-panel', width=12, lg=8
                     )
                ], no_gutters=True),
             ])

@app.callback([Output("monthly-repayment", "children"), Output("total-repayable", "children"), 
                #Output("total-interest", "children"),  
                Output("monthly-profit", "children")], 
              [Input("weight-interval", "n_intervals")])
def event_cb(data):
    
    summary_df = pd.read_sql_table("summary", con=engine, index_col='index')
    #monthly = pd.read_csv('monthly returns.csv')
    
    balance = summary_df['Closing balance'].iloc[-2]
    balance = "{:.2f}".format(round(balance, 2))
    month = round(summary_df['Returns'].iloc[-1], 2)
    profit = round(summary_df['Returns'].cumsum().iloc[-1], 2)
    
    return f'£{balance}', f'£{profit}', f'£{month}'

@app.callback(Output('full-data-card','children'), 
              [Input("weight-interval", "n_intervals")])
def event_s(data):
    portfolio = portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day']).sort_values(['Trading day','Trading time'], ascending=False)
    
    portfolio = portfolio[['Ticker Symbol', 'Type', 'Shares', 'Price', 'Total amount', 'Trading day']]
    
    return build_table(portfolio)

@app.callback(Output('graphy','figure'), 
              [Input("ticker-dropdown", "value")])
def event_a(ticker):
    return performance_chart(ticker)

@app.callback(Output('profit-graph','figure'), 
              [Input("chart-dropdown", "value")])
def event_b(chart):
        
    options = {'Goals' : goal_chart,
           'Monthly' : period_chart,
           'Dividends' : dividend_chart,
           'Cumulative' : cumsum_chart,
           'Profit/Loss' : profit_loss_chart,
           'Daily' : period_chart,
           'Weekly' : period_chart,
           'Quarterly' : period_chart,
           'Fiscal Year': period_chart,
    }
        
    if chart == 'Monthly':
        param = 'M'
        return options[chart](param)
    elif chart == 'Daily':
        param = 'D'
        return options[chart](param)
    elif chart == 'Weekly':
        param = 'W'
        return options[chart](param)
    elif chart == 'Quarterly':
        param = 'Q'
        return options[chart](param)
    elif chart == 'Fiscal Year':
        param = 'A-APR'
        return options[chart](param)
        
    fig = options[chart]()
    
    return fig

# @app.callback(
#     [Output('graph-block', 'hidden'), Output('graphy', 'figure'), Output('statss', 'hidden'), 
#      Output('monthly-repayment', 'children'), Output('total-repayable', 'children'),
#      Output('total-interest', 'children'), Output('full-data-card','children'), 
#      Output('advice', 'children')], 
#     [Input('loan-amount', 'value'), Input('interest-rate', 'value'), Input('term-length', 'value')])
# def update_slider(amount, rate, length):
#     # if 0 in (amount, rate, length) or None in (amount, rate, length):
#     #     pass
#     # else:
#     # amount = 1000         
#     # rate = 3.9
#     # length = 12
#     # try:
#     tmp = total_monthly_payment(amount, rate, length)
#     # except ZeroDivisionError:
#     #     return True, build_fig(df), False, format_amount(tmp), format_amount(principal_interest), format_amount(df['Total Interest'].iloc[-1]), build_table(df), guide

#     df = amortization(amount, rate, length)
#     summary = pd.read_csv('Investment Portfolio.csv', parse_dates=['Trading day'], dayfirst=True).sort_values(['Trading day','Trading time'], ascending=False)
    
#     principal_interest = amount + df['Total Interest'].iloc[-1]
        
#     if length > 6:
#         length2 =  randint(round(length/4), length-1)
#         df2 = amortization(amount, rate, length2)
#         savings = df['Total Interest'].iloc[-1] - df2['Total Interest'].iloc[-1]
#         guide = advice(length2, savings)
#     elif length > 1:
#         length2 =  length - 1
#         df2 = amortization(amount, rate, length2)
#         savings = df['Total Interest'].iloc[-1] - df2['Total Interest'].iloc[-1]
#         guide = advice(length2, savings)
#     else:
#         guide = 'Hi there!! Enter some details so we can calculate your loan payment.'
    
#     return False, build_fig(df), False, format_amount(tmp), format_amount(principal_interest), format_amount(df['Total Interest'].iloc[-1]), build_table(summary), guide

# def button():
#     return html.Div([dbc.Button([html.Span(className='fab fa-github icon')], className='fixed-btn', href='https://github.com/addenergyx/cf-coding-challenge', external_link=True)], className='button-container')

def Homepage():
    return html.Div([
            body,
            #button()
            html.Div(Fab()),
        ], id='background')

"""
Set layout to be a function so that for each new page load                                                                                                       
the layout is re-created with the current data, otherwise they will see                                                                                                     
data that was generated when the Dash app was first initialised
"""     

#app.scripts.config.serve_locally=True
app.layout = Homepage()

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
    #app.run_server()

















