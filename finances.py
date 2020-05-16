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
from dash.dependencies import Input, Output, State
import numpy as np
import os
from calendar import monthrange
import time
from typing import List
from plaid import Client as PlaidClient
import plotly.graph_objs as go
import plotly.express as px
from data import get_tokens
from plaid import errors as PlaidErrors
from datetime import datetime, timedelta, date
from starlingbank import StarlingAccount
from pandas.tseries.offsets import BMonthEnd
import base64
import re
import dash_table
import base64

data = get_tokens()

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')
PLAID_ENV = os.getenv('PLAID_ENV', 'development')
client = PlaidClient(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV)

STARLING_API_TOKEN = os.getenv('STARLING_API_TOKEN')

## Using starlingbank api wrapper
starling_account = StarlingAccount(STARLING_API_TOKEN)

rotation = 0

def progress_bar_color(progress):
    ## Changing progress bar colour
    if progress >= 100:
        color = "success"
    elif progress >= 60:
        color = "primary"
    elif progress >= 30:
        color = "warning"
    else:
        color = "danger"
    return color

def get_some_transactions(access_token: str, start_date: str, end_date: str) -> List[dict]:
    return client.Transactions.get(access_token, start_date, end_date)['transactions']

def num_of_card_transations(transactions: list):
    num = 0
    excluded_categories = ['Credit', 'Transfer']
    for a in transactions:
        if excluded_categories[0] not in a['category'] and excluded_categories[1] not in a['category']:
            if a['amount'] < 0:
                num+=1
    return num

def num_of_direct_debt(transactions: list):
    num = 0
    for a in transactions:
        if 'special' in a['category'] and a['amount'] > 0:
            num+=1
    return num

def initial_baby_step_2():
    debt, limit = total_debt()
       
    progress = 100 - int(( debt / limit) *100)
    
    colour = progress_bar_color(progress)    
    
    return progress, colour

def initial_weekly():
    
    today = datetime.now().date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    
    total = 0
    
    ## TODO: edit to include credit cards
    for i, account in data.iterrows():        
        weeks_transactions = client.Transactions.get(account['access_token'], str(start), str(end))['transactions']
        
        for transaction in weeks_transactions:
            ## Plaid's ML Categorisation is not accurate for some transactions
            ## Transfers between bank accounts will cancel eachother out
            
            #if 'transfer' not in transaction['transaction_code']:
            # print(account['bank'])
            # print(transaction['amount'])
            total = total + transaction['amount']
            
    return "£{:.2f}".format(abs(total))

def format_amount(value):
    if value >= 0:
        return '£{:,.2f}'.format(value)
    else:
        return '-£{:,.2f}'.format(abs(value))

def update_balances():
    balances = {}
    
    for i, account in data.iterrows():        
        try:
            #accounts = client.Accounts.balance.get(account['access_token'])['accounts']
            
            bank = client.Accounts.balance.get(account['access_token'])
            accounts = bank['accounts']
            ins_id = bank['item']['institution_id']
        
        except PlaidErrors.PlaidError as e:
            print(e)
            print(account['bank'])
            pass
        
        for row in accounts:
            if row['subtype'] == 'checking':
                logo = client.Institutions.get_by_id(ins_id, _options={ 'include_display_data': True })['institution']['logo']
                
                if logo is None:
                    path = 'assets/img/'
                    folder = os.listdir(path)
                    for image_filename in folder:
                        if re.search(account['bank'], image_filename, re.IGNORECASE):
                            logo = base64.b64encode(open('{0}{1}'.format(path, image_filename), 'rb').read()).decode()
                            break

                balances[f"{account['bank']}"] = {'balance':row['balances']['current'],
                                                  'logo':logo}
        # Update Starling bank data
        starling_account.update_balance_data()
        logo = client.Institutions.search('starling', _options={ 'include_display_data': True })['institutions'][0]['logo']
        balances['Starling Bank'] = { 'balance':starling_account.cleared_balance,
                                     'logo':logo }
                                     
    return balances

def total_debt():
    
    debt = 0
    limit = 0
    
    for i, account in data.iterrows():        
        try:
            accounts = client.Accounts.balance.get(account['access_token'])['accounts']
        except PlaidErrors.PlaidError as e:
            print(account['bank'])
            print(e)
            pass
        for row in accounts:
            if row['subtype'] == 'credit card':
                debt = debt + row['balances']['current']
                limit = limit + row['balances']['limit']
            elif row['balances']['current'] < 0:
                debt = debt - row['balances']['current']
                limit = limit + row['balances']['limit']
        
    return debt, limit

# import clearbit

# clearbit.key = 'sk_dcc7faddab234fdad32edfedff3f4564'

# company = clearbit.Company.find(domain='tesco.com', stream=True)
# if company != None:
#     print ("Name: " + company['name'] + " " + company['logo'])


def generate_transactions_table():
    
    today = datetime.now().date()
    start = today - timedelta(days=today.weekday())
    
    lis = []
        
    for i, account in data.iterrows():        
        transactions = client.Transactions.get(account['access_token'], str(start), str(today))['transactions']
        
        for transaction in transactions:
            row = [datetime.strptime(transaction['date'], '%Y-%m-%d').strftime('%d/%m/%y'), transaction['name'], transaction['amount']]
            lis.append(row)

    asl = pd.DataFrame(lis, columns=['Date', 'Payee', 'Amount'])
    
    asl.sort_values(by=['Date'], ascending=False, inplace=True)
    
    return html.Div(
        [
            html.Table(
                [
                    html.Tr(
                        [
                            html.Td(
                                html.P(row.values[0], className='balances')
                            ),
                            html.Td(
                                html.P(row.values[1], className='balances')
                            ),
                            html.Td(
                                html.P(format_amount(row.values[2]), className='balances'), className='amount'
                            )
                        ]    
                    )
                    for i, row in asl.iterrows()
                ], className="hover-table"
            ), 
        ], style={"height": "250px", "overflowY": "scroll", "overflowX": "hidden",'margin-bottom':'30px' }, className='large-2'
        )

def investments():
    
    ini = []
    today = datetime.now().date()
    
    for i, account in data.iterrows():        
        transactions = client.Transactions.get(account['access_token'], str(today.replace(day=1)), str(today))['transactions']
        for transaction in transactions:
            if re.search('vanguard', transaction['name'], re.IGNORECASE) or re.search('trading212', transaction['name'], re.IGNORECASE):
                row = [datetime.strptime(transaction['date'], '%Y-%m-%d').strftime('%d/%m/%y'), account['bank'], transaction['name'], transaction['amount']]
                ini.append(row)
    
    inves = pd.DataFrame(ini, columns=['Date', 'Account', 'Investment', 'Amount'])
    
    inves.sort_values(by=['Date'], ascending=False, inplace=True)
    
    return html.Div(
        [
            html.Table(
                [
                    html.Tr(
                        [
                            html.Td(
                                html.P(row.values[0], className='balances', style={'font-size':'10px'})
                            ),
                            html.Td(
                                html.P(row.values[1], className='balances', style={'font-size':'10px', 'text-align':'center'})
                            ),
                            html.Td(
                                html.P(row.values[2], className='balances', style={'font-size':'10px','width':'50%', 'text-align':'center'})
                            ),
                            html.Td(
                                html.P(format_amount(row.values[3]), className='balances', style={'font-size':'10px'}), className='amount'
                            )
                        ],    
                    )
                    for i, row in inves.iterrows()
                ], style={'width':'100%'}
            ), 
        ], style={"height": "150px", "overflowY": "scroll", "overflowX": "hidden",'margin-bottom':'5px' }, className='large-2'
        )
    
def generate_balances_table():
    
    #accounts = dict(sorted(update_balances().items(), key=lambda x: x[1], reverse=True))
    
    from collections import OrderedDict

    accounts = OrderedDict(sorted(update_balances().items(), key=lambda i: i[1]['balance'], reverse=True))
    
    # accounts = dict(sorted(balances.items(), key=lambda x: x['balance'], reverse=True))

    return html.Div(
        [
            html.Div(
                html.Table(
                    # Header
                    # [html.Tr([html.Th('Bank'), html.Th('Amount'),])]
                    # +
                    # Body
                    [
                        html.Tr(
                            [
                                html.Td(
                                    [
                                        html.Img(src='data:image/png;base64,{}'.format(value['logo']), style={'width':'100%'}, alt=" ")
                                    ], style={'width':'10%'},
                                ),
                                html.Td(
                                    html.P(key, className='balances', style={'margin-left':'5px'})
                                ),
                                html.Td(
                                    html.P(format_amount(value['balance']), className='balances'), className='amount'
                                ),
                                html.P("adfdasfdasf", id="hidden-{}".format(key), hidden=True)
                            ], style={'height': '50px'}, id=key    
                            
                        )for key, value in accounts.items()
                    ], className="hover-table", style={"overflow": "auto"}, id='tabs'
                ),
                #style={"height": "100px", "overflowY": "scroll"},
            ),
        ],
        #style={"height": "100%"},
        )

## Plaid categorises direct debits for each bank differently
    
def num_of_direct_debt(transactions: list):
    num = 0
    for a in transactions:
        if 'Debit' in a['category'] and a['amount'] > 0:
            num+=1
    return num

def num_of_direct_debt_coop(transactions: list):
    num = 0
    for a in transactions:
        if 'special' in a['transaction_type'] and a['amount'] > 0:
            num+=1
    return num

def minimum_payment(transactions: list):
    
    total = 0
    
    for a in transactions:
       if a['amount'] < 0:
           total = total + a['amount']*-1
    
    # progress = int(( total / 800) *100)
    
    return total

def build_bar(current, goal):
    
    progress = int(( current / goal) *100)
    
    return progress, f"{progress}%" if progress >= 10 else "", progress_bar_color(progress)

def coop_check():
    
    currentMonth = '{:02d}'.format(datetime.now().month) # Using int() here changes format of month, need leading 0 
    currentYear = datetime.now().year
    lastDay = monthrange(int(currentYear),int(currentMonth))[1]
    
    transactions = get_some_transactions(os.getenv('COOP_ACCESS_TOKEN'), "{0}-{1}-01".format(currentYear,currentMonth), 
                                          "{0}-{1}-{2}".format(currentYear,currentMonth,lastDay))
    
    mp = minimum_payment(transactions)
    dd = num_of_direct_debt_coop(transactions)
    ct = num_of_card_transations(transactions)
    
    p1, p2, p3 = build_bar(mp, 800)
    p4, p5, p6 = build_bar(dd, 4)
    p7, p8, p9 = build_bar(ct, 30)

    return p1, p2, p3, p4, p5, p6, p7, p8, p9 

p1, p2, p3, p4, p5, p6, p7, p8, p9 = coop_check()

def barclays_check():
    
    currentMonth = '{:02d}'.format(datetime.now().month) # Using int() here changes format of month, need leading 0 
    currentYear = datetime.now().year
    
    access_token = data.query('bank in "Barclays"')['access_token'].values[0]
    
    today = date.today()
    
    transactions = get_some_transactions(access_token, "{0}-{1}-01".format(currentYear,currentMonth), str(today))
    
    mp = minimum_payment(transactions)
    dd = num_of_direct_debt(transactions)
    
    p11, p12, p13 = build_bar(mp, 800)
    p14, p15, p16 = build_bar(dd, 2)

    return p11, p12, p13, p14, p15, p16

p11, p12, p13, p14, p15, p16 = barclays_check()

external_stylesheets =['https://codepen.io/IvanNieto/pen/bRPJyb.css', dbc.themes.BOOTSTRAP, 
                       'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css']

app = dash.Dash(external_stylesheets=external_stylesheets, 
                meta_tags=[
                    { 'name':'viewport','content':'width=device-width, initial-scale=1' },## Fixes media query not showing
                    {
                        'name': 'description',
                        'content': 'Personal Finance Dashboard'
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
        <style>
            #myDIV {
              width: 100%;
              padding: 50px 0;
              text-align: center;
              background-color: lightblue;
              margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div></div>
        {%app_entry%}
        <footer> 
          {%config%} 
          {%scripts%} 
          {%renderer%}
          <script>
            function myFunction() {
              var x = document.getElementById("myDIV");
              if (x.style.display === "none") {
                x.style.display = "block";
              } else {
                x.style.display = "none";
              }
            }
          </script>
        </footer>
    </body>
</html>
'''

app.title = 'Digital Dashboard - Finance'

colors = {
    'background':'#101727',
    'text':'#FFFFFF',
    'card':'#172144',
    'grad1':'#D30E92',
    'grad2':'#1E1572'
}

categorises_card = [
    dbc.CardHeader("Finance Fun Facts", style={'textAlign':'center', 'color':colors['text']}),
    dbc.CardBody(
        [
            html.Div(id='facts'),
        ], style={'color':colors['text']}
    ),
]

monthly_card = [
    dbc.CardHeader("Monthly Spend", style={'textAlign':'center', 'color':colors['text']}),
    dbc.CardBody(
        [
            dcc.Graph(id='monthly-fig')
        ], style={'color':colors['text'], 'padding':'0px'}
    ),
]

weekly_card = [
    dbc.CardHeader("This Week You Spent", style={'textAlign':'center', 'color':colors['text']}),
    dbc.CardBody(
        [
            #dcc.Loading(
                html.H2(children=[initial_weekly()], id="weekly-total", className="card-title"),
            #),
            html.A("See More >", id='see-more', hidden=True),
            html.Div(generate_transactions_table(), id='transactions', hidden=False)
        ], style={'color':colors['text'], 'textAlign':'center'},
    ),
]

balance_card = [
    dbc.CardHeader("Current Accounts", style={'textAlign':'center', 'color':colors['text']}),
    dbc.CardBody(
        [
            generate_balances_table()
        ], 
    ),
]                    

credit_card = [
    dbc.CardHeader("Credit Score", style={'textAlign':'center', 'color':colors['text']}),
    dbc.CardBody(
        [
            #html.H2('Hi', className="card-title"),
            dcc.Graph(id='credit-fig', #style={'width': '100vw', 'height': '50vh', 'position': 'absolute'}
                      ),
        ], style={'color':colors['text']}
    ),
]

progress1 = html.Div([
                    dbc.Row([
                        dbc.Col([                            
                            html.P("Pay in a minimum of £800", style={'margin':'0 auto', 'color': colors['text']}),
                        ], className="center"),
                        dbc.Col([
                            dbc.Progress(id="a", children=[p2], color=p3, value=p1, striped=True, animated=True),                    
                        ]),
                    ], className="align-items-center"),
                    dbc.Row([
                        dbc.Col([
                            html.P("Pay out at least four Direct Debits", style={'margin':'0 auto', 'color': colors['text']}),
                        ]),
                        dbc.Col([
                            dbc.Progress(id="b", children=[p5], color=p6, value=p4,striped=True, animated=True),
                        ]),
                    ], className="align-items-center"),
                    dbc.Row([
                        dbc.Col([
                            html.P("Number of card transactions", style={'margin':'0 auto', 'color': colors['text']}),
                        ]),
                        dbc.Col([
                            dbc.Progress(id="c", children=[p8], color=p9, value=p7, striped=True, animated=True),
                        ]),
                    ], className="align-items-center"),       
    ], id="aaa")

progress2 = html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.P("Pay in a minimum of £800", style={'margin':'0 auto', 'color': colors['text']}),
                        ], className="center"),
                        dbc.Col([
                            dbc.Progress(id="d", children=[p12], color=p13, value=p11, striped=True, animated=True),                    
                        ]),
                    ], className="align-items-center"),
                    dbc.Row([
                        dbc.Col([
                            html.P("Pay out at least two Direct Debits", style={'margin':'0 auto', 'color': colors['text']}),
                        ]),
                        dbc.Col([
                            dbc.Progress(id="e", children=[p15], color=p16, value=p14,striped=True, animated=True),
                        ]),
                    ], className="align-items-center"),      
    ], id="bbb")

# def barclays_check():
#     mp = minimum_payment(transactions, 800)
#     dd = num_of_direct_debt(transactions, 2)
#     return

coop_card = [
    dbc.CardHeader("Bank Rewards", style={'textAlign':'center', 'color':colors['text']}),

    dbc.CardBody(
        [
            html.Div([
                dbc.Button("Co-operative Bank", id="cooop", active=True),
                dbc.Button("Barclays Bank", id="barclays")
            ], className="btn-group btn-group-sm center", style={"padding-bottom":"10px"}),
            
            # daq.ToggleSwitch(
            #     id='my-toggle-switch',
            #     value=False
            # ),
            # dbc.Row([
            #     dbc.Col([
            #         ,
            #     ]),
            #     dbc.Col([
            #         ,
            #     ]),
            # ], id="bank-buttons-row"),
            #html.H2(id="coop", style={'textAlign':'center'}),
            html.Div(id='container-button-timestamp')
            # progress,
            # progress2
        ], style={'color':colors['text']}
    ),
]

baby_step_1 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("£1000 Emergency Fund", style={'color': colors['text'] }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-1", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
                html.P("helloooooooooooooooooooooooooooooooo", id='hidden-baby-step-1', hidden=False, style={'color': colors['text'] }),
            ], id='baby-step-1', className="baby-step-spacing")     

progress, colour = initial_baby_step_2()

baby_step_2 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Pay Off Debt", style={'color': colors['text'] }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-2", color=colour, value=progress, striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
                html.P("helloooooooooooooooooooooooooooooo", id='hidden-baby-step-2', hidden=False, style={'color': colors['text'] }),
            ], id='baby-step-2', className="baby-step-spacing")

baby_step_3 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("3 Month Emergency Fund", style={'color': colors['text'], }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-3", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
            ], id='baby-step-3', className="baby-step-spacing")

baby_step_4 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Invest 15%", style={'color': colors['text'], }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-4", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
                html.Div( investments(), id='hidden-baby-step-4', hidden=False),
            ], id='baby-step-4', className="baby-step-spacing")

baby_step_5 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Kids University fund", style={'color': colors['text'], }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-5", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
            ], id='baby-step-5', className="baby-step-spacing")

baby_step_6 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Pay Off Mortgage", style={'color': colors['text'], }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-6", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"),
            ], id='baby-step-6', className="baby-step-spacing")

baby_step_7 = html.Div([
                dbc.Row([
                    dbc.Col([
                        html.P("Build Wealth And Give", style={'color': colors['text'], }, className='balances'),
                    ]),
                    dbc.Col([
                        dbc.Progress(id="progress-7", color="primary", striped=True, animated=True),
                    ]),
                ], className="align-items-center"), 
            ], id='baby-step-7', className="baby-step-spacing")

body = html.Div(
    [
       dbc.Row(
           [
               ## Baby Steps Panel
               dbc.Col(
                  [
                     html.Div([
                         html.H2("Dave Ramsey's Baby Steps",style={'text-align':'center', 'padding-bottom':'10px'}),
                    ], style={'color': colors['text'], 'border-bottom':'2px solid', 'margin-bottom':'30px' }),
                    
                    html.Div([
                        baby_step_1,
                        baby_step_2,
                        baby_step_3,
                        baby_step_4,
                        baby_step_5,
                        baby_step_6,
                        baby_step_7,
                        ], #style={'padding-right':'20px','padding-left':'20px'}
                    ),
                    
                ], width=12,lg=3, className='card grad', style={ 'padding':'20px', #'height':'100vh'
                                                           } 
                ),
              
              ## Main Panel
              dbc.Col(
                  [
                    dbc.Row(
                    [
                      dbc.Col(dbc.Card(monthly_card, className='card-style'), width=12),
                    ],
                    ),
                    dbc.Row(
                    [
                      dbc.Col(dbc.Card(coop_card, className='card-style',
                                       #style={'background-color':'red'}
                                       ), width=12, lg=4),
                      dbc.Col(dbc.Card(weekly_card, className='card-style'), width=12, lg=4),
                      dbc.Col(dbc.Card(categorises_card, className='card-style'), width=12, lg=4),
                    ],
                    ),
                    dbc.Row(
                    [
                      dbc.Col(dbc.Card(balance_card, className='card-style'), width=12, lg=4),
                      #dbc.Col(dbc.Card(days_card, className='card-style'), width=12, lg=4),
                      dbc.Col(dbc.Card(credit_card, className='card-style'), width=12, lg=8),
                    ],
                    ),
                  ],width=12, lg=9
                  
            ),
            ## Update
            dcc.Interval(id="progress-interval", n_intervals=0, interval=600000),
            dcc.Interval(id="facts-interval", n_intervals=0, interval=60000),
       ]),
       
  ])

@app.callback(Output('container-button-timestamp', 'children'),
              [Input('cooop', 'n_clicks'), Input('barclays', 'n_clicks')])
def displayClick(btn1, btn2):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'cooop' in changed_id:
        bars = progress1
    elif 'barclays' in changed_id:
        bars = progress2
    else:
        bars = progress1  
    return html.Div(bars)

# @app.callback(
#     Output("hidden-Barclays", "hidden"),
#     [Input("tabs", "n_clicks")],
#     [State("hidden-Barclays", "hidden")],
# )
# def toggle_accounts(n_click, state):
#     print(dash.callback_context.triggered)
#     if state is True:
#         return False
#     return True
                                                              
@app.callback(
    [Output("see-more", "hidden"), Output("transactions", "hidden")],
    [Input("see-more", "n_clicks"), Input("transactions", "n_clicks")],
    [State("see-more", "hidden"), State("transactions", "hidden")],
)
def toggle_see_more(n_click, n_click2, state, state2):
    if state is True:
        return False, True
    return True, False

@app.callback(
    Output("hidden-baby-step-1", "hidden"),
    [Input("baby-step-1", "n_clicks")],
    [State("hidden-baby-step-1", "hidden")],
)
def toggle_step(n_click, state):
    if state is True:
        return False
    return True

@app.callback(
    Output("hidden-baby-step-4", "hidden"),
    [Input("baby-step-4", "n_clicks")],
    [State("hidden-baby-step-4", "hidden")],
)
def toggle_step_4(n_click, state):
    print(n_click)
    if n_click == 0:
        return True
    if state is True:
        return False
    return True

@app.callback(
    Output("hidden-baby-step-2", "hidden"),
    [Input("baby-step-2", "n_clicks")],
    [State("hidden-baby-step-2", "hidden")],
)
def toggle_step_2(n_click, state):
    if state is True:
        return False
    return True

@app.callback(Output("weekly-total","children"), [Input("progress-interval", "n_intervals")])
def update_weekly(n):
    return initial_weekly()


@app.callback(Output("facts","children"), [Input("facts-interval", "n_intervals")])
def update_facts(n):
    
    global rotation
    rotation = rotation + 1
    
    
    today = datetime.now().date()
    
    
    if rotation == 2:
        
    
        ## Investment in pizza
        investment = 0
        
        for i, account in data.iterrows():        
            transactions = client.Transactions.get(account['access_token'], str(today.replace(day=1)), str(today))['transactions']
            for transaction in transactions:
                if re.search('vanguard', transaction['name'], re.IGNORECASE) or re.search('trading212', transaction['name'], re.IGNORECASE):
                    investment = investment + transaction['amount']
    
        pizza = 19.99
        num_of_pizza_missed = round(investment / pizza)
        
        image_filename = 'assets/img/pizza.png'
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
        
        return html.Div(
            [
                html.P("Your Savings/Investments this month could of bought...", className='mainSpan'),
                html.Div(
                    [
                        html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width':'100px', }),
                        html.P(f"~{num_of_pizza_missed}"),
                        html.P("Domino's Pizzas")
                    ], className='hoverSpan', style={'margin':'0 auto'}
                )
            ], style={'text-align':'center', 'display': 'flex', 'align-items': 'center'}
        )
    
    elif rotation == 1:
        ## Top 5
        print("2")
        image_filename = 'assets/img/shopping.png'
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
            
        lis = []
            
        for i, account in data.iterrows():        
            transactions = client.Transactions.get(account['access_token'], str(today.replace(day=1)), str(today))['transactions']
            
            for transaction in transactions:
                row = [datetime.strptime(transaction['date'], '%Y-%m-%d').strftime('%d/%m/%y'), transaction['name'], account['bank'], transaction['amount'], transaction['category']]
                lis.append(row)
        
        asl = pd.DataFrame(lis, columns=['Date', 'Payee', 'Bank','Amount', 'category'])
        
        aw = asl.groupby('Payee', as_index=False).Amount.sum()
        
        fillter = aw['Payee'].str.contains('adenij|STO|MOBILE-CHANNEL|DAVID', case=False)
        
        aw = aw[~fillter]
            
        ## TODO: Look into using machine learning to predict if a transaction is internal is not
        
        payees = ['Trading212','Chip','Amazon', 'ASDA', 'Tesco', 'PayPal', 'Iceland', 'Vanguard']
        
        for payee in payees:
            ff = aw[aw['Payee'].str.contains(payee, case=False)].sum()
            ff['Payee'] = payee
            aw = aw[~aw['Payee'].str.contains(payee, case=False)]
            aw = aw.append(ff, ignore_index=True)
        
        aw = aw[aw['Amount'] > 0]
        
        ## Top 5 Merchs
        merch_freq = asl[~asl['Payee'].str.contains('adenij|pot|fund', case=False)]['Payee'].value_counts()
        merch_freq = merch_freq.nlargest(5).reset_index(level=0)
        merch_freq.rename(columns={"Payee":"Count","index": "Payee"}, inplace=True)
        
        fig = px.pie(merch_freq, values='Count', names='Payee')
        
        fig.update_layout(
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=0,
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        print("2")
        return html.Div(
                [
                    html.Div(
                        [
                            html.P("Top 5 Merchants..."),
                            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width':'100px', })
                        ], className='mainSpan int-box'
                    ),
                    html.Div(
                        [
                            dcc.Graph(figure=fig),
                        ], className='hoverSpan', #style={'margin':'0 auto'}
                    ),
                ], className="ext-box",
            )
    else:
        rotation = 0
        coop_transactions = get_some_transactions(os.getenv('COOP_ACCESS_TOKEN'), str(today.replace(day=1)), str(today))
        num = num_of_card_transations(coop_transactions)
        image_filename = 'assets/img/card.png'
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())
        print("3")
        return html.Div(
                [
                    html.Div(
                        [
                            html.P("Times you've used your card this month..."),
                            
                        ], className='mainSpan'
                    ),
                    html.Div(
                        [
                            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width':'100px', }),
                            html.P(f"{num} coop card transactions this month"),
                        ], className='hoverSpan', style={'margin':'0 auto'}
                    )
                ], style={'text-align':'center', 'display': 'flex', 'align-items': 'center'}
            )
    


    # ## Opportunity cost


    
    # dash_table.DataTable(
    #     id='table',
    #     columns=[{"name": i, "id": i} for i in merch_freq.columns],
    #     style_as_list_view=True,
    #     data=merch_freq.to_dict('records'),
    #     style_table={'color': 'white', 'overflowY': 'auto', 'overflowX': 'hidden'},
    #     style_data={'color':'white'},
    #     style_header={'backgroundColor': '#101727'},
    #     fixed_rows={ 'headers': True, 'data': 0 },
    #     style_cell={
    #         'backgroundColor': '#101727',
    #         'color': 'white',
    #         #'minWidth': '80px', 
    #         'width': '50%', 
    #         #'maxWidth': '100px', 
    #         'font_size': '16px',
    #         'textAlign':'center',
    #     },
    # )
    
    return "Missing Data"



# @app.callback(
#     [Output("progress", "value"), Output("progress", "children"), Output("progress", "color")],
#     [Input("progress-interval", "n_intervals")],
# )
# def update_coop_progress(n):
    
#     # check progress of some background process, in this example we'll just
#     # use n_intervals constrained to be in 0-100
#     currentMonth = '{:02d}'.format(datetime.now().month) # Using int() here changes format of month, need leading 0 
#     currentYear = datetime.now().year
#     lastDay = monthrange(int(currentYear),int(currentMonth))[1]
    
#     coop_transactions = get_some_transactions(os.getenv('COOP_ACCESS_TOKEN'), "{0}-{1}-01".format(currentYear,currentMonth), 
#                                               "{0}-{1}-{2}".format(currentYear,currentMonth,lastDay))

#     num = num_of_card_transations(coop_transactions)
#     progress = int(( num / 30) *100)
    
#     # only add text after 10% progress to ensure text isn't squashed too much
#     return progress, f"{progress} %" if progress >= 10 else "", num, progress_bar_color(progress)

@app.callback(
    [Output("progress-1", "value"), Output("progress-1", "children"), Output("progress-1", "color")],
    [Input("progress-interval", "n_intervals")],
)
def update_baby_step_1(n):
    
    ## Get Emergency Fund balance from monzo pot
    a = data[data['bank'] == 'Monzo']
    b = a['access_token'].values[0]
    
    for account in client.Accounts.balance.get(b)['accounts']:
        if account['name'] == 'Emergency Fund':
            current = account['balances']['available']
            break
    
    # starling_account.update_savings_goal_data()        
    # emergency_fund = starling_account.savings_goals['a980e84c-8ad3-466a-9bfd-d82d25a291a5']
    # current = emergency_fund.total_saved_minor_units
    
    #progress = int(( current / 1000) *100)
        
    # only add text after 10% progress to ensure text isn't squashed too much
    return build_bar(current, 1000)
    #progress, f"{progress}%" if progress >= 10 else "", progress_bar_color(progress)


@app.callback(
    [Output("progress-2", "value"), Output("progress-2", "children"), Output("progress-2", "color")],
    [Input("progress-interval", "n_intervals")],
)
def update_baby_step_2(n):
    
    debt, limit = total_debt()
       
    progress = 100 - int(( debt / limit) *100)
        
    return progress, f"{progress}%" if progress >= 10 else "", progress_bar_color(progress)


@app.callback(
    [Output("progress-3", "value"), Output("progress-3", "children"), Output("progress-3", "color")],
    [Input("progress-interval", "n_intervals")],
)
def update_baby_step_3(n):
        
    # starling_account.update_savings_goal_data()
    # emergency_fund = starling_account.savings_goals['a980e84c-8ad3-466a-9bfd-d82d25a291a5']
    # current = emergency_fund.total_saved_minor_units
    # goal = emergency_fund.target_minor_units
    
    a = data[data['bank'] == 'Monzo']
    b = a['access_token'].values[0]
    
    for account in client.Accounts.balance.get(b)['accounts']:
        if account['name'] == 'Emergency Fund':
            current = account['balances']['available']
            break
    
    #progress = int((current / 3900) *100)
        
    # only add text after 10% progress to ensure text isn't squashed too much
    return build_bar(current, 3900)


@app.callback(
    [Output("progress-4", "value"), Output("progress-4", "children"), Output("progress-4", "color")],
    [Input("progress-interval", "n_intervals")],
)
def update_baby_step_4(n):
    
    # start = datetime.date.today()
    # end = datetime.date(start.year+2, 12, 31)

    # from dateutil.relativedelta import relativedelta
    # today = date.today()
    # d = today - relativedelta(months=1)
    # start = date(d.year, d.month, 1)
    # end = date(today.year, today.month, 1) - relativedelta(days=1)
    # last_bussiness_day = pd.date_range(start, end, freq='BM')

    ## Get monthly salary
    
    today = date.today()
    offset = BMonthEnd()
    #Last business day of previous month
    last_bussiness_day = offset.rollback(today).date()
    
    access_token = data.query('bank in "Barclays Student"')['access_token'].values[0]
    
    transactions = get_some_transactions(access_token, str(last_bussiness_day), str(last_bussiness_day))
    
    pay = 0
    
    import re
    for transaction in transactions:
        if re.search('PA Consulting', transaction['name'], re.IGNORECASE):
            pay = pay + transaction['amount']*-1
    
    goal_investment = round(pay*.15, 2)
    
    ## Get all investments for current month
    
    current_investment = 0
    for i, account in data.iterrows():        
        transactions = client.Transactions.get(account['access_token'], str(today.replace(day=1)), str(today))['transactions']
        for transaction in transactions:
            if re.search('vanguard', transaction['name'], re.IGNORECASE) or re.search('trading212', transaction['name'], re.IGNORECASE):
                current_investment = current_investment + transaction['amount']
        
    return build_bar(current_investment, goal_investment)

## Make an update button

@app.callback( Output("credit-fig", "figure"), [Input("progress-interval", "n_intervals")])
def update_credit_graph(n):
    
    cred = pd.read_csv(r'D:\OneDrive\GitHub\bank-to-ynab\credit.csv')
    
    
    trace0 = go.Scatter(x=cred['Month'], y=cred['Experian Credit Score'],
                    mode='lines',
                    name='Experian',
                    line = {'color':'#52e5ec'},
                    #fill='tozeroy'
                    )
    
    trace1 = go.Scatter(x=cred['Month'], y=cred['Credit Karma (TransUnion)'],
                    mode='lines',
                    name='TransUnion',
                    line = {'color':'#eb1054'},
                    #fill='tozeroy'
                    )

    trace2 = go.Scatter(x=cred['Month'], y=cred['Clear Score (Equifax)'],
                    mode='lines',
                    name='Equifax',
                    line = {'color':'#C2FF0A'},
                    #fill='tozeroy'
                    )
    
    data = [trace0, trace1, trace2]
    
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                        font={
                             'family': 'Courier New, monospace',
                             'size': 18,
                             'color': 'white'
                             },
                       # title=title,
                        xaxis={'gridcolor':'rgb(46,47,47)','autorange': True,},
                        yaxis={'gridcolor':'rgb(46,47,47)','autorange': True,},
                       hovermode='closest',
                       autosize=False,
                       margin=dict(
                            l=0,
                            r=0,
                            b=0,
                            t=0,
                        ),
                       # transition={
                       #      'duration': 500,
                       #      'easing': 'cubic-in-out',}
                       )
    
    fig = go.Figure(data=data, layout=layout)
    
    fig.update_layout(
        legend=dict(
            x=0.01,
            y=1,
            traceorder="normal",
            font=dict(
                family="sans-serif",
                size=12,
                color="#f7f7f7"
            ),

            bgcolor="#292b2c",
            bordercolor="#f7f7f7",
            borderwidth=2,
        )
    )

    return fig

@app.callback( Output("monthly-fig", "figure"), [Input("progress-interval", "n_intervals")])
def update_spend_graph(n):
    
    data = get_tokens()
    
    currentYear = datetime.now().year
    currentMonth = datetime.now().month
    
    lastDay = monthrange(int(currentYear),int(currentMonth))[1]
    
    start_date = date(currentYear, datetime.now().month, 1)
    end_date = date(currentYear, datetime.now().month, lastDay)   
    
    monthly_transactions = pd.DataFrame()
    last_months_transactions = pd.DataFrame()

    
    for i, account in data.iterrows():        
        transactions = get_some_transactions(account['access_token'], str(start_date), str(end_date))
        for transaction in transactions:
            monthly_transactions = monthly_transactions.append(transaction, ignore_index=True)
    
    monthly_transactions.amount.describe()

    #https://stackoverflow.com/questions/30857680/pandas-resampling-error-only-valid-with-datetimeindex-or-periodindex
    data = monthly_transactions.set_index('date')
    data.index = pd.to_datetime(data.index)

    #https://stackoverflow.com/questions/41625077/python-pandas-split-a-timeserie-per-month-or-week
    weeks = [g for n, g in data.groupby(pd.Grouper(freq='W'))]

    months = [g.reset_index for n, g in data.groupby(pd.Grouper(freq='M'))]

    df = weeks[0]
    df.reset_index(inplace=True)
    
    m2 = monthly_transactions.groupby(['date'])['amount'].sum()
    
    ## Fill missing dates
    m2.index = pd.PeriodIndex(m2.index, freq='D')
    
    m3 = m2.reindex(pd.period_range(start_date, datetime.today().date()), fill_value=0.0)
    
    m4 = m3.cumsum()    
    
    # x = '2020-05-01'
    
    # monthly_transactions[monthly_transactions['date']==x]
    
    # text = ['{}: {}'.format(i[1]['name'], i[1]['amount']) for i in monthly_transactions.iterrows() if i[1]['date'] == x]
    
    dates = [start_date + timedelta(days=x) for x in range((end_date-start_date).days + 1)]

    trace0 = go.Scatter(x=dates, y=m4,
                    mode='lines',
                    name='Spending',
                    line = {'color':'#FFFFFF'},
                    fill='tozeroy',
                    # hovertemplate =
                    #     '<i>Price</i>: $%{y:.2f}'+
                    #     '<br><b>X</b>: %{monthly_transactions} == %{x}] }<br>'+
                    #     '<b>%{customdata}</b>',
                    # text = ['Custom text {}'.format(i + 1) for i in range(5)],
                    )
    
    
    trace1 = go.Scatter(x=dates, y=[1000] * len(dates),
                    mode='lines',
                    name='Budget',
                    line = {'color':'#D30E92','dash':'dot'},
                    #fill='tozeroy'
                    )

    # trace2 = go.Scatter(x=cred['Month'], y=cred['Clear Score (Equifax)'],
    #                 mode='lines',
    #                 name='Equifax',
    #                 line = {'color':'#C2FF0A'},
    #                 #fill='tozeroy'
    #                 )
    
    data = [trace0, trace1]
    
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
                       plot_bgcolor='rgba(0,0,0,0)',
                        # font={
                        #      'family': 'Courier New, monospace',
                        #      'size': 18,
                        #      'color': 'white'
                        #      },
                        xaxis={    
                            'showgrid': False, # thin lines in the background
                            'zeroline': False, # thick line at x=0
                            'visible': False,  # numbers below
                            'tickmode':'linear',
                        },                                                
                        yaxis={    
                            'showgrid': False,
                            'zeroline': False,
                            'visible': False,
                        },
                       autosize=False,
                       margin=dict(
                             l=0,
                             r=0,
                             b=0,
                             t=3,
                       ),
                       # transition={
                       #      'duration': 500,
                       #      'easing': 'cubic-in-out',}
                       )
    
    fig = go.Figure(data=data, layout=layout)
    
    fig.update_layout(
        height=200,
        hovermode='x unified',
        showlegend=False,
        # legend=dict(
        #     x=0.01,
        #     y=1,
        #     traceorder="normal",
        #     font=dict(
        #         family="sans-serif",
        #         size=12,
        #         color="#f7f7f7"
        #     ),
        #     bgcolor="#292b2c",
        #     bordercolor="#f7f7f7",
        #     borderwidth=2,
        # )
    )

    return fig
                                                           
def Homepage():
    layout = html.Div([
        body,
    ], style={'backgroundColor': colors['background']}, className='layzout')
    return layout

app.layout = Homepage()

if __name__ == "__main__":
    #app.run_server()
    app.run_server(debug=True, use_reloader=False)

























