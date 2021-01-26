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
#import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from visuals import *
#performance_chart, ml_model, period_chart, goal_chart, profit_loss_chart, cumsum_chart, dividend_chart, return_treemap, convert_to_gbp, get_holdings
from components import Fab
from server import server
import os
from sqlalchemy import create_engine
from jobs import updates
from newsapi import NewsApiClient

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

portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day']).sort_values(['Trading day','Trading time'], ascending=False)
equities = pd.read_sql_table("equities", con=engine, index_col='index')

# def update_news(ticker):
#     # Init
#     newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
    
#     # /v2/top-headlines
#     top_headlines = newsapi.get_top_headlines(q=ticker,
#                                               #sources='google-news',
#                                               language='en',
#                                               #country='gb'
#                                               )
    
#     articles = top_headlines['articles']
    
#     titles = []
#     urls = []
#     for a in articles:
#         titles.append(a['title'])
#         urls.append(a['url'])
    
#     d = {'Title':titles,'Url':urls}
    
#     news_df = pd.DataFrame(d)

#     return news_df

# df = update_news('BFT')

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

map_card = [
                html.Div([            
                   #dcc.Loading(
                        dcc.Graph(id='treemap-graph'#, figure=return_treemap()
                                  )
                    #)
                ], id='treemap-block', hidden=False)
             ]

stats_card = [
                dbc.CardBody(
                    [
                        html.H2('Results'),
                        html.P("This Month's Opening Balance"),
                        html.Strong(html.P(id='monthly-repayment', className='result')),
                        html.P('Total Realised P/L'),
                        html.Strong(html.P(id='total-profit', className='result')),
                        html.P("This Month's Realised P/L"),
                        html.Strong(html.P(id='monthly-profit', className='result')),
                        # html.P('Floating P/L'),
                        # html.Strong(html.P(id='floats', className='result'))
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

def company(x):
    try:
        company = equities[equities['INSTRUMENT'] == x]['COMPANY'].values[0]
        dic = {'label': f'{company} ({x})', 'value': x}
    except:
        dic = {'label': str(x), 'value': x}
    return dic

tickers = [company(x) for x in portfolio['Ticker Symbol'].drop_duplicates()]

# tickers = []
# for x in portfolio['Ticker Symbol'].drop_duplicates():
#     try:
#         company = equities[equities['INSTRUMENT'] == x]['COMPANY'].values[0]
#         tickers.append({'label': f'{company} ({x})', 'value': x})
#     except:
#         tickers.append({'label': str(x), 'value': x})

#tickers = [{'label':str(x), 'value': x} for x in portfolio['Ticker Symbol'].drop_duplicates()]

charts = [{'label':str(x), 'value': x} for x in ['Goals', 'Monthly', 'Dividends', 'Cumulative', 'Profit/Loss', 'Daily', 'Weekly', 'Yearly', 'Quarterly', 'Fiscal Year']]
maps = [{'label':str(x), 'value': x} for x in ['Day', 'Portfolio']]

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
                                    id='map-dropdown',
                                    options=maps,
                                    value='Day',
                                    clearable=False,
                                    style={'margin-top':'50px'}
                                  ),
                              ]), 
                            
                              html.Div(
                                   [
                                  dcc.Dropdown(
                                    id='ticker-dropdown',
                                    options=tickers,
                                    value=tickers[0]['value'],
                                    searchable=True,
                                    style={'margin-top':'50px'}
                                  ),
                              ]),
                              
                              html.Div(
                                   [
                                  html.Button(
                                    'Update Portfolio',
                                    id='update-btn',
                                    style={'margin-top':'50px'}
                                  ),
                              ]),
                              
                           ], id='side-panel', width=12, lg=2
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
                                       dbc.Col(html.Div(map_card), width=12),
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
                                                    
                               dcc.Interval(id="stats-interval", n_intervals=0, interval=60000),
                               dcc.Interval(id="map-interval", n_intervals=0, interval=10000),
                               dcc.Interval(id="dropdown-interval", n_intervals=0, interval=7200000),
                               html.Div(id='container-button-basic', hidden=True)
                              
                           ], id='main-panel', width=12, lg=9
                     )
                ], no_gutters=True),
             ])

@app.callback([Output("monthly-repayment", "children"), Output("total-profit", "children"), 
                #Output("total-interest", "children"),  
                Output("monthly-profit", "children"), Output("monthly-profit", "style")], 
              [Input("stats-interval", "n_intervals")])
def event_cb(data):
    
    summary_df = pd.read_sql_table("summary", con=engine, index_col='index')
    
    balance = summary_df['Closing balance'].iloc[-2]
    balance = "{:.2f}".format(round(balance, 2))
    month_profit = round(summary_df['Returns'].iloc[-1], 2)
    total_profit = "{:.2f}".format(round(summary_df['Returns'].cumsum().iloc[-1], 2))
    
    style = {'color': 'green'} if month_profit > 0 else {'color': 'red'}
    month = f'£{"{:.2f}".format(month_profit)}' if month_profit > 0 else f'-£{"{:.2f}".format(abs(month_profit))}'
    
    return f'£{balance}', f'£{total_profit}', f'{month}', style

# @app.callback(Output("floats", "children"),
#               [Input("weight-interval", "n_intervals")])
# def event(data):
    
#     holdings = get_holdings()
#     holdings['UK MARKET VALUE'] = ''
#     holdings = holdings.apply(convert_to_gbp, axis=1)
    
#     #sum(holdings['MARKET VALUE'])
    
#     balance = "{:.2f}".format(round(sum(holdings['UK MARKET VALUE']), 2))
    
#     return f'£{balance}'

@app.callback(
    Output('container-button-basic', 'children'),
    [Input('update-btn', 'n_clicks')])
def update_output(n_clicks):
    print(n_clicks)
    if n_clicks is None:
        return ''
    # live_portfolio()
    updates()
    return ''

@app.callback(
    [Output('ticker-dropdown', 'options'), Output('full-data-card','children')],
    [Input('dropdown-interval', 'n_intervals')])
def update_tickers(n_clicks):
    
    portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day']).sort_values(['Trading day','Trading time'], ascending=False)
    tickers = [company(x) for x in portfolio['Ticker Symbol'].drop_duplicates()]
    portfolio = portfolio[['Ticker Symbol', 'Type', 'Shares', 'Price', 'Total amount', 'Trading day']]

    return tickers, build_table(portfolio)

# @app.callback(Output('full-data-card','children'), 
#               [Input("dropdown-interval", "n_intervals")])
# def event_s(data):
#     portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day']).sort_values(['Trading day','Trading time'], ascending=False)
    
#     portfolio = portfolio[['Ticker Symbol', 'Type', 'Shares', 'Price', 'Total amount', 'Trading day']]
    
#     return build_table(portfolio)
    
@app.callback(Output('graphy','figure'), 
              [Input("ticker-dropdown", "value")])
def event_a(ticker):
    return performance_chart(ticker)

@app.callback(Output('treemap-graph','figure'), 
              [Input("map-dropdown", "value"), Input("map-interval", "n_intervals")])
def event_o(option, ticks):
    if option == 'Portfolio':
        return return_treemap()
    return day_treemap()

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
           'Yearly': period_chart,
           'Quarterly' : period_chart,
           'Fiscal Year': period_chart,
    }
    
    # Seperated from options dict because running all functions takes time
    if chart == 'Monthly':
        param = 'M'
        return options[chart](param)
    elif chart == 'Daily':
        param = 'D'
        return options[chart](param)
    elif chart == 'Weekly':
        param = 'W'
        return options[chart](param)
    elif chart == 'Yearly':
        param = 'Y'
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
    app.run_server(debug=True, use_reloader=False) # https://community.plotly.com/t/keep-updating-redrawing-graph-while-function-runs/8744
    #app.run_server()

















