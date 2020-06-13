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
from components import Fab
from withings_api import WithingsAuth, WithingsApi, AuthScope
from withings_api.common import get_measure_value, MeasureType
import myfitnesspal
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import datetime as dt
from server import server
import re
import os

## Remove when in production as it's in wsgi.py
from dotenv import load_dotenv
load_dotenv(verbose=True, override=True)


external_stylesheets =['https://codepen.io/IvanNieto/pen/bRPJyb.css', dbc.themes.BOOTSTRAP, 
                       'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.0/css/all.min.css']

app = dash.Dash(name='fitness', server=server, url_base_pathname='/fitness/', external_stylesheets=external_stylesheets, assets_ignore='dash.css',
                meta_tags=[
                    { 'name':'viewport','content':'width=device-width, initial-scale=1' },
                    {
                        'name': 'description',
                        'content': 'This dashboard is designed to aid in my new year resolution of being healthier.'
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

app.title = 'Digital Dashboard - Fitness'

app.config.suppress_callback_exceptions = True

## Withings API

# auth = WithingsAuth(
#     client_id='b12142ab4ac3d4f87a0fb285aa1aba6eb7b44124c294e6f763b2245dc825c4eb',
#     consumer_secret='c2d3b5ffc786300e388d3bbf5b750ee5490f243ecea5f4dac3f46dfd82a47a4a',
#     callback_uri='http://127.0.0.1:8050/fitness/',
#     #mode='demo',  # Used for testing. Remove this when getting real user data.
#     scope=(
#         AuthScope.USER_ACTIVITY,
#         AuthScope.USER_METRICS,
#         AuthScope.USER_INFO,
#         AuthScope.USER_SLEEP_EVENTS,
#     )
# )

# # Have the user goto authorize_url and authorize the app. They will be redirected back to your redirect_uri.
# authorize_url = auth.get_authorize_url()

# print(authorize_url)

# credentials = auth.get_credentials('9ef398077ade293bcf56005ea792d5bfcc68d1fa')

# # Now you are ready to make calls for data.
# api = WithingsApi(credentials)

# meas_result = api.measure_get_meas() ## All measurements

# weight = get_measure_value(meas_result, with_measure_type=MeasureType.WEIGHT)
# fat_mass = get_measure_value(meas_result, with_measure_type=MeasureType.FAT_MASS_WEIGHT)
# bf = get_measure_value(meas_result, with_measure_type=MeasureType.FAT_RATIO)
# muscle_mass = get_measure_value(meas_result, with_measure_type=MeasureType.MUSCLE_MASS)

client = myfitnesspal.Client(os.getenv('MFP_USER'), os.getenv('MFP_PASS'))

## Measurements ##

measurements = client.get_measurements('Weight') # By default gets a month
current_weight  = list(measurements.values())[0]

## https://www.myfitnesspal.com/measurements/check_in
bf_measurements = client.get_measurements('Body Fat %')
current_bf = list(bf_measurements.values())[0]


user_metadata = client.user_metadata
#weight_goal = user_metadata['goal_preferences']['weight_goal']['value']
#rate_weight_loss = user_metadata['goal_preferences']['weight_change_goal']['value']
starting_weight = user_metadata['profiles'][0]['starting_weight']['value']

streak = user_metadata['system_data']['login_streak']

max_rate_fat_loss = 69 # kcal/kg
goal_bf = 12

# Recommended rate of weight lose is 1% body weight per week
rate_weight_loss = .01*current_weight 

## Vitruvian Physique Guide

current_lean_body_mass = current_weight*(100-current_bf)/100
goal_lean_body_mass = current_lean_body_mass*.97

goal_weight = goal_lean_body_mass / (1-goal_bf*0.01)

weight_loss_to_six_pack = current_weight - goal_weight
weeks_to_six_pack = weight_loss_to_six_pack / rate_weight_loss

today = datetime.today().date()
days_to_six_pack = timedelta(weeks=weeks_to_six_pack)

goal_date = today + days_to_six_pack


## Jeremy Ethier Guide

current_body_fat = current_weight*current_bf / 100
max_daily_caloric_deficit = current_body_fat*max_rate_fat_loss
fat_per_week = (max_daily_caloric_deficit*7)/(35000*2.2)

def get_icon(number):
    return 'fas fa-angle-double-up' if number > 0 else 'fas fa-angle-double-down'

def build_card(title, total, difference, fig, icon, colour): 
    return dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(html.P(f"Today's {title}".upper(), className='title')),
                    dbc.Col(html.P([html.Span(className=icon, style={'margin-right':'10px'}), difference], className='diff-text'), style={'color':colour}),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.H2(total)),
                    dbc.Col(dcc.Graph(id=f'{title}-fig', figure=fig, className='graph')),
                ], className='align-items-end'
            )
        ]
    )

def build_marco_cards(macro):
        
    return html.Div(
            [
                 dbc.Row([
                     dbc.Col(html.P(f'{macro}'.capitalize(), style={'float':'left'})), 
                     dbc.Col(html.P(id=f'{macro}-total', style={'float':'right'}))
                 ]),
                 dbc.Row(dbc.Col([dbc.Progress(id=f'progress-bar-{macro}')])),
            ], className='card summary-card', style={'padding':'20px'}
        )

marcos = html.Div(
    [
        html.H2('Macros', id='macros-title'),
        build_marco_cards('proteins'),
        build_marco_cards('carbs'),
        build_marco_cards('fats'),
        
        # html.Div(
        #     [
        #          dbc.Row([
        #              dbc.Col(html.P('Proteins', style={'float':'left'})), 
        #              dbc.Col(html.P(id='proteins-total', style={'float':'right'}))
        #          ]),
        #          dbc.Row(dbc.Col([dbc.Progress(id='proteins', color='primary')])),
        #     ], className='card summary-card', style={'padding':'20px'}
        # ),
        # html.Div(
        #     [
        #          dbc.Row([html.P('Fats', style={'float':'left'}), html.P(id='fats-total', style={'float':'right'})]),
        #          dbc.Row([dbc.Progress(id='fats', color='warning')]),
        #     ], className='card summary-card'
        # ),
        # html.Div(
        #     [
        #          dbc.Row([html.P('Carbohydrates', style={'float':'left'}), html.P(id='carbs-total', style={'float':'right'})]),
        #          dbc.Row([dbc.Progress(id='carbs', color='danger')]),
        #     ], className='card summary-card'
        # )
         # dbc.Progress(id='proteins', color='success'),
         # dbc.Progress(id='fats', color='danger')
    ], #className='card summary-card'
)


def build_mini_fig(data, colour):
    
    mini = int(min(data) - 1)
    maxi = int(max(data) + 1)
    
    trace0 = go.Scatter(x=list(range(len(data))), y=data[::-1], 
                    mode='lines',
                    name='Spending',
                    line = {'color': colour, 'shape': 'spline', 'smoothing': 1},
                    fill='tozeroy',
                    )
    
    data = [trace0]
        
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
                            'range':[mini, maxi],
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
                        )
    
    fig = go.Figure(data=data, layout=layout)
    
    fig.update_layout(
        height=60,
        width=120,
        hovermode='x',
        showlegend=False,
    )
    
    return fig

def bar_fig(df):
    
    dates = df['date']
    
    # fig = px.bar(df, x="date", y='calories')
    colors = {'breakfast':'yellow',
              'lunch':'orange',
              'dinner':'darkorange',
              'snacks':'maroon',
              '':'',
              '':'',
              '':'',
              '':'',}
    
    
    traces = [go.Bar(name=a, 
                     x=dates,
                     y=df[a],
                     marker_color=colors[a])
              for a in df.columns[1:]]
        
    layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)',
                    font={
                          #'family': 'Courier New, monospace',
                          #'size': 18,
                          'color': 'grey'
                          },
                    xaxis={    
                        'showgrid': False, # thin lines in the background
                        'zeroline': False, # thick line at x=0
                        #'visible': False,  # numbers below
                        #'tickmode':'linear',
                        #'autorange':False,
                    },                                                
                    yaxis={
                        #'showgrid': False,
                        'zeroline': False,
                        #'visible': False,
                        'gridcolor':'grey'
                    },
                    autosize=False,
                    margin=dict(
                          l=0,
                          r=0,
                          b=0,
                          t=0,
                    ),
                )
    
    fig = go.Figure(data=traces, layout=layout)

    fig.update_layout(
        barmode='group',
        bargap=0.3, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1, # gap between bars of the same location coordinate.
    )

    return fig

def build_fig(data, colour):
    
    mini = int(min(data) - 5)
    maxi = int(max(data) + 5)
    
    print(mini, maxi)
    
    if colour != '#FFFFFF':
        
        ## 7 Day moving average
        window_size = 7
        moving_averages = data[::-1].rolling(window_size)
        
        moving_averages = moving_averages.mean().tolist()
        
        ## Removes nan
        moving_averages = moving_averages[window_size:]
        
        trace1 = go.Scatter(x=list(range(len(data))), y=moving_averages,
                mode='lines',
                name='Moving Average',
                line = {'color':'#01BEA4', 'shape': 'spline', 'smoothing': 1},
                #fill='tozeroy'
                )
    
        trace0 = go.Scatter(x=list(range(len(data[window_size:]))), y=data[::-1][window_size:], 
                mode='lines',
                name='Actual',
                line = {'color': colour, 'shape': 'spline', 'smoothing': 1},
                fill='tozeroy',
                )
        
        data = [trace0, trace1]

    else:
    
        mini = int(min(data) - 5)
        maxi = int(max(data) + 5)
        
        print('side bar')
        print(mini, maxi)
        
        trace0 = go.Scatter(x=list(range(len(data))), y=data[::-1], 
                        mode='lines',
                        #name='Kg',
                        line = {'color': colour, 'shape': 'spline', 'smoothing': 1},
                        fill='tozeroy',
                        )
    
        data = [trace0]
        
        
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
                            'range':[mini, maxi],
                            #'showgrid': False,
                            'zeroline': False,
                            'visible': False,
                        },
                        autosize=False,
                        margin=dict(
                              l=0,
                              r=0,
                              b=0,
                              t=0,
                        ),
                        )
    
    fig = go.Figure(data=data, layout=layout)
    
    fig.update_layout(
        # height=60,
        #width=300,
        hovermode='x',
        showlegend=False,
    )
    
    return fig

def inches(part='Chest'):
        
    may = dt.date(2020, 5, 1) # Started taking measurements in May
    
    ## Measurements are returned as ordered dictionaries. The first argument specifies the measurement name, 
    ## which can be any name listed in the MyFitnessPal Check-In page.
    
    body_parts = ['Right Bicep', 'Left Bicep', 'Waist', 'Neck', 'Shoulders', 'Chest', 'Left Forearm', 
                  'Right Forearm', 'Left Thigh', 'Right Thigh', 'Left Calf', 'Right Calf']
    
    body_part_options = [{'label':str(body_part), 'value': body_part} for body_part in body_parts]
    
    measurements = client.get_measurements(part, may, datetime.today().date())
    
    #df = pd.DataFrame(measurements, index=[0])
    
    df = pd.DataFrame.from_dict(measurements, orient='index')
    
    fig = build_fig(df[0], '#FFFFFF')
    
    return fig
# html.Div(
#         [
#             html.Div(
#                 dcc.Dropdown(
#                     id='measurements-dropdown',
#                     options=body_part_options,
#                     value=part,
#                 ),
#             ),
#             html.Div(
#                 dcc.Graph(figure=fig, id='inches-fig')
#             )
#         ], id='inches-card'
#     )

body_parts = ['Right Bicep', 'Left Bicep', 'Waist', 'Neck', 'Shoulders', 'Chest', 'Left Forearm', 
              'Right Forearm', 'Left Thigh', 'Right Thigh', 'Left Calf', 'Right Calf']
    
body_part_options = [{'label':str(body_part), 'value': body_part} for body_part in body_parts]

def meals_table(date=datetime.today()):
    
    ## Foods highest in cals
    dict_ = {}
    
    #date = datetime.today() - timedelta(days=2)
    
    day = client.get_date(date)

    #entry = day.meals[0].entries

    for meals in day.meals:
        for entry in meals:
            if entry.name in dict_:
                dict_[entry.name.capitalize()] += entry.totals['calories'] #if 'calories' in meal.totals.keys() else 0
            else: 
                dict_[entry.name.capitalize()] = entry.totals['calories']

    ordered_food = {key: dict_[key] for key in sorted(dict_, key=dict_.get, reverse=True)}

    return html.Div(
    [
        html.Div(
            [
                dcc.DatePickerSingle(
                    id='my-date-picker-single',
                    min_date_allowed=datetime(2017, 1, 1),
                    max_date_allowed=datetime.today(),
                    #initial_visible_month=datetime.today(),
                    display_format='DD/MM/Y',
                    date=str(date),
                    #style={'border-radius':'20px'}
                ),                
            ], style={'text-align':'center', 'margin-bottom':'10px'}),
        html.Div(
            [
                html.Table(
                    [
                        html.Tr(
                            [
                                html.Td(
                                    html.P(food, className='balances'), **{'data-label': 'Food'} #data-*={'label':"Due Date"}
                                ),
                                html.Td(
                                    html.P(total, className='balances'), **{'data-label': 'Total'} #data*={'label':"Account"}
                                ),
                            ]    
                        )
                        for food, total in ordered_food.items()
                    ], className="transaction-table", id='food-table'
                ),
            ], className='table-block', #style={"height": "100%", "overflowY": "scroll", "overflowX": "hidden"},
        )
    ], id='logs'
    )


def activity_table():
    
    lis = []
    
    for i in range(0,5):
        date = datetime.today() - timedelta(days=i)
        day = client.get_date(date)
        #day.exercises[1].get_as_list()

        for dict_ in day.exercises[0].get_as_list():
            if dict_['nutrition_information']['calories burned'] != 0 and dict_['nutrition_information']['minutes'] != None:
                lis.append([date.strftime('%d-%m-%Y'), 
                            dict_['name'], 
                            '{} ({})'.format(dict_['nutrition_information']['calories burned'], dict_['nutrition_information']['minutes'])
                            ])

    asl = pd.DataFrame(lis, columns=['Date','Activity', 'Calories Burned (Minutes)'])

    return html.Div(
    [
        html.Table(
            [
                html.Tr(
                    [
                        html.Td(
                            html.P(row.values[0], className='balances'), **{'data-label': 'Date'} #data-*={'label':"Due Date"}
                        ),
                        html.Td(
                            html.P(row.values[1], className='balances'), **{'data-label': 'Activity'} #data*={'label':"Account"}
                        ),
                        html.Td(
                            html.P(row.values[2], className='balances'), className='amount', **{'data-label': 'Calories Burned (Minutes)'} #data*={'label':"Amount"}
                        ),
                    ]    
                )
                for i, row in asl.iterrows()
            ], className="hover-table transaction-table"
        ), 
    ], className='act-table-block', #style={"height": "100%", "overflowY": "scroll", "overflowX": "hidden"}, #className='large-2'
    )

def update_weight_card():

    colour = '#1450F0'
    
    measurements = client.get_measurements('Weight') # By default gets a month
    
    current_weight  = list(measurements.values())[0]
    yesterday_weight = list(measurements.values())[1]
            
    weights = pd.DataFrame.from_dict(measurements, orient='index')
    
    fig = build_mini_fig(weights[0][:14], colour)
    
    diff = round(current_weight - yesterday_weight, 2)
    
    icon = get_icon(diff)
    
    return build_card('weight', current_weight, diff, fig, icon, colour)

def update_big_weight():
    
    colour = '#b22222'
    
    today = datetime.today().date()
    
    days_ago = datetime.today().date() - timedelta(days=37)
    
    measurements = client.get_measurements('Weight', today, days_ago) # By default gets a month
            
    weights = pd.DataFrame.from_dict(measurements, orient='index')
            
    return build_fig(weights[0], colour)

def update_big_body_fat():
    
    colour = '#0055FC'
    
    bf_measurements = client.get_measurements('Body Fat %')
            
    bf = pd.DataFrame.from_dict(bf_measurements, orient='index')
        
    return build_fig(bf[0], colour)

def update_body_fat_card():

    colour = '#FFA500'
    
    bf_measurements = client.get_measurements('Body Fat %')
    current_bf = list(bf_measurements.values())[0]
    yesterday_bf = list(bf_measurements.values())[1]
            
    bf = pd.DataFrame.from_dict(bf_measurements, orient='index')
    
    fig = build_mini_fig(bf[0][:14], colour)
    
    diff = round(current_bf - yesterday_bf, 2)
    
    icon = get_icon(diff)
    
    return build_card('body fat %', current_bf, diff, fig, icon, colour)

def update_big_calories():
    
    #colour = '#FFA500'
    
    sort = 'meal' # add toggle or buttons
    
    ## Sort by meal
    if sort == 'meal':
        calories_dict = {}
        i = 0
        while len(calories_dict) < 30:    
            date = datetime.today() - timedelta(days=i)
            day = client.get_date(date)
            i = i + 1
            dayfood = {}
            for meal in day.meals:
                dayfood[meal.name] = meal.totals['calories'] if 'calories' in meal.totals.keys() else 0
                #calories_dict[date.date()] = {meal:meal['calories']}
                
            calories_dict[date.date()] = dayfood
        df = pd.DataFrame.from_dict(calories_dict, orient='index').rename_axis('date').reset_index()

    ## Sort by macro
    else:
        calories_dict = {}
        i = 0
        while len(calories_dict) < 30:    
            date = datetime.today() - timedelta(days=i)
            day = client.get_date(date)
            i = i + 1
            calories_dict[date.date()] = day.totals
            
        #df = pd.DataFrame(calories_dict)
        df = pd.DataFrame.from_dict(calories_dict, orient='index').rename_axis('date').reset_index()
        df['sodium'] = df['sodium'].div(1000)
        df.drop(['calories'], axis=1, inplace=True)
        
    ## line graph
    # cal_list = []
    # i = 0
    # while len(cal_list) < 30:
    #     date = datetime.today() - timedelta(days=i)
    #     day = client.get_date(date)
    #     i = i + 1
    #     cal_list.append( 0 if not day.totals else day.totals['calories']) 

    
    return bar_fig(df)

def update_calories_card():
    
    colour = '#1450F0'
    
    ## Food Intake ##
        
    cal_list = []
    i = 0
    while len(cal_list) < 8:
        date = datetime.today() - timedelta(days=i)
        day = client.get_date(date)
        i = i + 1
        cal_list.append( 0 if not day.totals else day.totals['calories']) 
    
    diff = round(cal_list[0] - cal_list[1], 2)
    
    icon = get_icon(diff)
    
    fig = build_mini_fig(cal_list, colour)
    
    return build_card('calories', cal_list[0], diff, fig, icon, colour)

def update_big_activity_card():
    
    colour = '#8A2BE2'

    activity_list = []
    i = 0
    while len(activity_list) < 38:
        date = datetime.today() - timedelta(days=i)
        day = client.get_date(date)
        i += 1
        calories_burned = 0
        if day.exercises[0].get_as_list():
            for a in day.exercises[0].get_as_list():
                calories_burned += a['nutrition_information']['calories burned']

        activity_list.append(calories_burned)

    return build_fig(pd.Series(activity_list), colour)


def update_activity_card():
    
    colour = '#FFA500'

    activity_list = []
    i = 0
    while len(activity_list) < 8:
        date = datetime.today() - timedelta(days=i)
        day = client.get_date(date)
        i += 1
        calories_burned = 0
        if day.exercises[0].get_as_list():
            for a in day.exercises[0].get_as_list():
                calories_burned += a['nutrition_information']['calories burned']

        activity_list.append(calories_burned) 

    diff = round(activity_list[0] - activity_list[1], 2)

    icon = get_icon(diff)

    fig = build_mini_fig(activity_list, colour)

    return build_card('activity', activity_list[0], diff, fig, icon, colour)

card = update_weight_card()
bf_card = update_body_fat_card()
cal_card = update_calories_card()
act_card = update_activity_card()

data_card = [
                dbc.CardHeader(id='data-title'),
                dcc.Loading(
                    dbc.CardBody(dcc.Graph(id='data-fig', className='sum-graph'),  style={'padding':'0px'})
                )
            ]

aaa = [
      dcc.Dropdown(
        id='measurements-dropdown',
        options=body_part_options,
        value='Chest',
        clearable=False,
        #style={'margin':'20px 10px'}
      ),
      dcc.Loading(
        dcc.Graph(id='inches-fig', style={'height':'400px'})
      )
      ]
# activity_card = [html.Div(activity_table(), id='acts-card')]

stats_card = [
                #dbc.CardBody(id='stats-card')
                html.Div(id='stats-card'),
            ]

inches_card = [html.Div(inches(), id='inches-card')]

theme =  {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
}

body = html.Div(
    [
       dbc.Row(
           [
               ## Side Panel
               dbc.Col(
                  [
                      html.H2('Goals', style={'text-align':'center'}),
                      html.Div(
                          [
                              daq.Gauge(
                                  size=200,
                                  showCurrentValue=True,
                                  units="KG",
                                  id='weight-gauge',
                                  min=goal_weight,
                                  max=starting_weight,
                                  value=current_weight,
                                  color="#FFA500",
                                  style={'text-align':'center'},
                              ),
                              daq.Gauge(
                                  size=200,
                                  showCurrentValue=True,
                                  units="Body Fat %",
                                  id='bf-gauge',
                                  min=12,
                                  max=25,
                                  value=current_bf,
                                  color="#47BAF3",
                                  style={'text-align':'center'},
                              ), 
                              daq.Gauge(
                                  size=200,
                                  showCurrentValue=True,
                                  units="Days to Goal",
                                  id='days-gauge',
                                  min=0,
                                  max=60,
                                  value=days_to_six_pack.days,
                                  color="#C62825",
                                  style={'text-align':'center'},
                              ),
                          ],
                      )
                      
                  ], id='side-panel', width=12, lg=2
               ),
              
              ## Main panel
              dbc.Col(
                  [
                      html.Div(html.H1('Overview')),
                      
                      dbc.Row(
                          [
                              dbc.Col(html.Div(dbc.Card(card, className='summary-card' ), id='weight-card'), width=12, md=6, lg=3),
                              dbc.Col(html.Div(dbc.Card(bf_card, className='summary-card'), id='bf-card'), width=12, md=6, lg=3),
                              dbc.Col(html.Div(dbc.Card(cal_card, className='summary-card'), id='calories-card'), width=12, md=6, lg=3),
                              dbc.Col(html.Div(dbc.Card(act_card, className='summary-card'), id='activity-card'), width=12, md=6, lg=3),
                          ], className = 'data-row'
                      ),
                      
                      #html.Br(),
                      
                      dbc.Row(
                          [
                              dbc.Col(dbc.Card(data_card, id='full-data-card', className='summary-card'), width=12, lg=8),
                              #dbc.Col(dbc.Card(id='side-data-card', className='summary-card'), width=12, lg=4),
                              dbc.Col(dbc.Card(stats_card, id='side-data-card', className='summary-card'), width=12, lg=4),
                              #dbc.Col(dbc.Card(aaa, id='test', className='summary-card'), width=12, lg=4),
                          ], className = 'data-row'
                      ),
                      
                      #html.Br(),
                      
                      dbc.Row(
                          [
                              dbc.Col([marcos], width=12),
                          ], className = 'data-row'
                      ),
                                            
                      dcc.Interval(id="weight-interval", n_intervals=0, interval=60000),
                      
                  ], id='main-panel', width=12, lg=9
            )
       ]),
       
  ])

# @app.callback(
#     Output('inches-card', 'children'),
#     [Input('measurements-dropdown', 'value')])
# def update_measurements(body_part):
#     print('--------------')
#     print(body_part)
#     return inches(body_part)
    
@app.callback(
    Output('inches-fig', 'figure'),
    [Input('measurements-dropdown', 'value')])
def update_measurements(body_part):
    return inches(body_part)

@app.callback(
    Output('side-data-card', 'children'),
    [Input('my-date-picker-single', 'date')])
def update_output(date):
    
    # dict_ = {}
    # ## Foods highest in cals
    # #date = datetime.today() - timedelta(days=i)
    
    # day = client.get_date(date)

    # #entry = day.meals[0].entries

    # for meals in day.meals:
    #     for entry in meals:
    #         if entry.name in dict_:
    #             dict_[entry.name.capitalize()] += entry.totals['calories'] #if 'calories' in meal.totals.keys() else 0
    #         else: 
    #             dict_[entry.name] = entry.totals['calories']
    
    # top5 = {key: dict_[key] for key in sorted(dict_, key=dict_.get, reverse=True)[:5]}

    date = datetime.strptime(re.split('T| ', date)[0], '%Y-%m-%d')
    
    return meals_table(date.date())


@app.callback( 
    [Output("progress-bar-carbs", "value"), Output("carbs-total", "children"), 
     Output("progress-bar-fats", "value"), Output("fats-total", "children"),
     Output("progress-bar-proteins", "value"), Output("proteins-total", "children"),
     #Output("macros-title", "children")
     ], 
    [Input("weight-interval", "n_intervals")])
def update_bars(n): 
    
    # Getting latest food input
    
    ## Use this method if only want last recorded day
    ## As I am currently alternative day fasting will get last recorded day
    # i = 0
    # date = datetime.today() - timedelta(days=i)
    # day = client.get_date(date)
    # while not day.totals:
    #     i = i + 1
    #     date = datetime.today() - timedelta(days=i)
    #     day = client.get_date(date)
    # daily_calories = day.totals
        
    date = datetime.today()
    day = client.get_date(date)
    daily_calories = day.totals
    
    date = '' if date == datetime.today() else date.date().strftime('%d/%m/%Y')
    
    if daily_calories:
        return daily_calories['carbohydrates']/day.goals['carbohydrates']*100 , f"{daily_calories['carbohydrates']}g/{day.goals['carbohydrates']}g", daily_calories['fat']/day.goals['fat']*100, f"{daily_calories['fat']}g/{day.goals['fat']}g", daily_calories['protein']/day.goals['protein']*100, f"{daily_calories['protein']}g/{day.goals['protein']}g"#, f'Macros {date}'

    return 0 , f"0g/{day.goals['carbohydrates']}g", 0, f"0g", 0, f"0g/{day.goals['protein']}g"

    
@app.callback( 
    [Output("data-title", "children"), Output("data-fig", "figure"), Output("stats-card", "children"), Output("side-data-card", "style")], 
    [Input("weight-card", "n_clicks"), Input("bf-card", "n_clicks"), 
     Input("calories-card", "n_clicks"), Input("activity-card", "n_clicks")]) #dbc.card doesn't have n_clicks prop
def update_main_card(btn1, btn2, btn3, btn4): 
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print([p['prop_id'] for p in dash.callback_context.triggered])
    
    if 'activity-card.n_clicks' in changed_id:
        return "Monthly Calories Burned", update_big_activity_card(), activity_table(), {'background-image': 'linear-gradient(to bottom right, #7525c0, #9f31ff)',
                                                                       'box-shadow': 'inset 12px 12px 24px #7525c0, inset -12px -12px 24px #9f31ff'}
    elif 'calories-card.n_clicks' in changed_id:
        return "Monthly Calories", update_big_calories(), meals_table(), {'background-image': 'linear-gradient(to bottom right, #d98c00, #ffbe00)',
                                                                       'box-shadow': 'inset 12px 12px 24px #d98c00, inset -12px -12px 24px #ffbe00'}
    elif 'bf-card.n_clicks' in changed_id:
        return "Monthly Body Fat", update_big_body_fat(), aaa, {'background-image': 'linear-gradient(to bottom right, #0054FE, #0061EB)',
                                                                       'box-shadow': 'inset 12px 12px 24px #0044a5, inset -12px -12px 24px #007eff',
                                                                       'padding':'0px'
                                                               }
    else:
        return "Monthly Weight", update_big_weight(), aaa, { 'background-image': 'linear-gradient(to bottom right, #971d1d, #cd2727)', 
                                                                   'box-shadow': 'inset 12px 12px 24px #971d1d, inset -12px -12px 24px #cd2727',
                                                                   'padding':'0px'
                                                           }

# @app.callback( Output("weight-fig", "figure"), [Input("weight-interval", "n_intervals")])
# def update_weight_graph(n):
#     measurements = client.get_measurements('Weight') # By default gets a month
    
#     weights = pd.DataFrame.from_dict(measurements, orient='index')

#     trace0 = go.Scatter(x=weights.index, y=weights[0],
#                 mode='lines',
#                 name='Spending',
#                 line = {'color':'#29E3A2', 'shape': 'spline', 'smoothing': 1},
#                 #fill='tozeroy',
#                 )
    
#     data = [trace0]
    
#     layout = go.Layout(paper_bgcolor='rgba(0,0,0,0)',
#                        plot_bgcolor='rgba(0,0,0,0)',
#                         # font={
#                         #      'family': 'Courier New, monospace',
#                         #      'size': 18,
#                         #      'color': 'white'
#                         #      },
#                         xaxis={    
#                             'showgrid': False, # thin lines in the background
#                             'zeroline': False, # thick line at x=0
#                             #'visible': False,  # numbers below
#                             #'tickmode':'linear',
#                         },                                                
#                         yaxis={
#                             #'range':[60,100],
#                             #'showgrid': False,
#                             'zeroline': False,
#                             #'visible': False,
#                         },
#                         autosize=False,
#                         margin=dict(
#                               l=0,
#                               r=0,
#                               b=0,
#                               t=3,
#                         ),
#                         )
    
#     fig = go.Figure(data=data, layout=layout)
    
#     fig.update_layout(
#         height=300,
#         width=300,
#         hovermode='x',
#         showlegend=False,
#         # legend=dict(
#         #     x=0.01,
#         #     y=1,
#         #     traceorder="normal",
#         #     font=dict(
#         #         family="sans-serif",
#         #         size=12,
#         #         color="#f7f7f7"
#         #     ),
#         #     bgcolor="#292b2c",
#         #     bordercolor="#f7f7f7",
#         #     borderwidth=2,
#         # )
#     )

#     return fig


# @app.callback(Output("pie-fig", "figure"), [Input("weight-interval", "n_intervals")])
# def update_macros_graph(n):

#     ## Food Intake ##

#     # Getting latest food input
#     i = 0
#     date = datetime.today() - timedelta(days=i)
#     day = client.get_date(date)
#     while not day.totals:
#         i = i + 1
#         date = datetime.today() - timedelta(days=i)
#         day = client.get_date(date)
#     daily_calories = day.totals
    
#     ## Sodium is in mg instead of g
#     daily_calories['sodium'] = daily_calories['sodium'] / 1000
        
#     daily_calories.pop('calories')
    
#     df = pd.DataFrame(list(daily_calories.items()), columns=['Macro', 'Grams'])
    
#     fig = px.pie(df, values='Grams', names='Macro')
        
#     fig.update_layout(
#         height=250,
#         showlegend=False,
#         margin=dict(
#             l=0,
#             r=0,
#             b=0,
#             t=0,
#         ),
#         paper_bgcolor='rgba(0,0,0,0)',
#         plot_bgcolor='rgba(0,0,0,0)',
#     )
    
#     return fig

def Homepage():
    return html.Div([
            body,
            html.Div(Fab()),
        ], id='background')

app.layout = Homepage()

if __name__ == "__main__":
    #app.run_server()
    app.run_server(debug=True, use_reloader=False)


























