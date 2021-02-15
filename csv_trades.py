# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 22:00:39 2021

@author: david
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')

engine = create_engine(db_URI)

##------------------------------- CSV -------------------------------##

# holdings = pd.read_sql_table("holdings", con=engine, index_col='index')
# og_returns = pd.read_sql_table("returns", con=engine, index_col='index')
# og_trades = pd.read_sql_table("trades", con=engine, index_col='index')

def upload():

    trades = pd.read_csv('data/data.csv')
    
    trades[['Trading day', 'Trading time']] = trades['Time'].str.split(' ', expand=True)
    trades['Type'] = trades['Action'].str.split(' ').str[1].str.capitalize()
    
    total = trades['Result (GBP)'].sum()
    
    trades.drop(['Time', 'Action', 'French transaction tax', 'Finra fee (GBP)', 
                 'Stamp duty (GBP)', 'Stamp duty reserve tax (GBP)', 'Transaction fee (GBP)'], inplace=True, axis=1)
    
    trades['Trading day'] = pd.to_datetime(trades['Trading day'])
    
    trades['Price'] = trades['Price / share'] / trades['Exchange rate']
    
    returns = trades.groupby(['Trading day']).sum()['Result (GBP)'].reset_index(level=0)
    
    gains = []
    losses = []
    
    days = trades['Trading day'].unique()
    for day in days:
        gain = 0
        loss = 0
        for x in trades[trades['Trading day'] == day]['Result (GBP)'].dropna():
            if x > 0:
                gain += x
            else:
                loss += x
        gains.append(gain)
        losses.append(loss)
    
    returns['Gains'] = gains
    returns['Losses'] = losses   
    
    returns.rename(columns={'Result (GBP)':'Returns', 'Trading day':'Date'}, inplace=True)
    
    trades.rename(columns={'Ticker':'Ticker Symbol', 'No. of shares':'Shares', 'Total (GBP)':'Total cost', 'ID':'Order ID',
                                  'Finra fee (GBP)':'Charges and fees', 'Currency (Price / share)': 'Currency Price / share',
                                  'Result (GBP)':'Result'}, inplace=True)
    
    # og_trades.to_sql('trades_og', engine, if_exists='replace')
    # og_returns.to_sql('returns_og', engine, if_exists='replace')
    
    trades.to_sql('trades', engine, if_exists='replace')
    returns.to_sql('returns', engine, if_exists='replace')
    
    # holdings_returns = missing_data.groupby(['Ticker']).sum()['Result (GBP)'].reset_index(level=0)
    
    # gains = []
    # losses = []
    
    # for ticker in ret['Ticker']:
    #     gain = 0
    #     loss = 0
    #     for x in missing_data[missing_data['Ticker'] == ticker]['Result (GBP)'].dropna():
    #         if x > 0:
    #             gain += x
    #         else:
    #             loss += x
    #     gains.append(gain)
    #     losses.append(loss)
    
    # holdings_returns['Gains'] = gains
    # holdings_returns['Losses'] = losses























