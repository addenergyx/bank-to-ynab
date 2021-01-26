# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 12:23:51 2021

@author: david
"""

import imaplib
import os
import email
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import stockstats
import collections
from pandas_datareader import data as web
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prettytable import PrettyTable
import re
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go
from pytrends.request import TrendReq
from sqlalchemy import create_engine
from pytrends import dailydata

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

# ------------------------------------------------           
#
# Calculates total portfolio returns and individual stock returns
# Trading212 currently doesn't show total returns of individual stocks
# Averages are in GBP
#
# ------------------------------------------------

def returns():

    trades = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day'])
    
    # all_holdings = trades['Ticker Symbol'].unique()
    
    ## Getting all tickers and isin from portfolio
    temp_df = trades.drop_duplicates('Ticker Symbol')
    
    all_holdings = temp_df[['Ticker Symbol', 'ISIN']] 
    
    # watchlist = ['NIO','SMAR','RDW','PYPL','NFLX', 'RVLV', 'SMWH', 'AMZN', 'GOOGL', 'MCD', 'MSFT', 'AAPL', 'FB', 
    #              'WMT', 'KIE', 'WPC', 'SHOP', 'UBER', 'MTCH', 'JD.', 'DLR', 'CARD', 'FSLY', 'WKHS', 'RMV', 'TW.', 'PSN', 'MU', 'AMD']
    
    # def returnNotMatches(a, b):
    #     return [x for x in b if x not in a]
    
    # ## Remove stocks already in my portfolio
    # watchlist = returnNotMatches(all_holdings['Ticker Symbol'].tolist(), watchlist)
    
    total_returns = 0
    
    holdings_dict = collections.defaultdict(dict) # Allows for nesting easily
    returns_dict = collections.defaultdict(dict)
    
    averages = pd.DataFrame(columns=['Trading day', 'Ticker Symbol', 'Average', 'Exchange rate'])
    
    for symbol in all_holdings['Ticker Symbol'].tolist():
            
        df = trades[trades['Ticker Symbol'] == symbol]
        
        df = df.reset_index().drop('index', axis=1)
            
        a = df[df.Type == 'Sell']
        
        print(f'-------{symbol}-------')
        
        for ii, sell_row in a.iterrows():
            
            ## currently does not take into account fees 
            ## should use total cost column instead later
            
            share_lis = df['Shares'][:ii+1].tolist()
            price_lis = df['Price'][:ii+1].tolist()
            type_lis = df['Type'][:ii+1].tolist()
            day_lis = df['Trading day'][:ii+1].tolist()
            fx_lis = df['Exchange rate'][:ii+1].tolist()
    
            #fees_lis = df['Charges and fees'][:ii+1].tolist()
        
            c = 0
            x = 0
            holdings = 0
            average = 0
                    
            for s, p, t, d, fx in list(zip(share_lis, price_lis, type_lis, day_lis, fx_lis)):
                
                if t == 'Buy':
                    c += s*p
                    holdings += s
                    average = c / holdings
                    
                    averages.loc[len(averages)] = [d, symbol, average, fx]
                    
                    print(f'Buy Order: {s} @ {p}')
                    print(f'New Holdings Average: {holdings} @ {average}')
                
                else:
                    ## Selling stock
                    
                    ## if ii == len(share_lis): <- Doesn't work, This is probably because in the Python 3.x, 
                    ## zip returns a generator object. This object is not a list
                    ## https://stackoverflow.com/questions/31011631/python-2-3-object-of-type-zip-has-no-len/38045805
        
                    if ii == x:
                        
                        average = c / holdings
                        gain_loss = p - average
                        total_profit = gain_loss * s
                        print(f'Current Holdings Average: {holdings} @ {average}')
                        print(f'Final Sell Order: {s} @ {p}')
                        print(f'Total Return on Invesatment: {round(total_profit, 2)}')
                        total_returns += round(total_profit, 2)
                        
                        if symbol in holdings_dict:
                            # returns_dict[symbol] += total_profit
                            
                            if total_profit > 0:
                                holdings_dict[symbol]['Gains'] += total_profit
                            else:
                                holdings_dict[symbol]['Losses'] += total_profit
                            
                            holdings_dict[symbol]['Gross Returns'] += total_profit
                            
                        else:
                            # returns_dict[symbol] = total_profit
                            
                            if total_profit > 0:
                                holdings_dict[symbol]['Gains'] = total_profit
                                holdings_dict[symbol]['Losses'] = 0
                            else:
                                holdings_dict[symbol]['Losses'] = total_profit
                                holdings_dict[symbol]['Gains'] = 0
                            
                            holdings_dict[symbol]['Gross Returns'] = total_profit
                                                  
                        if d in returns_dict:    
                            returns_dict[d]['Returns'] += total_profit
                            
                            if total_profit > 0:
                                returns_dict[d]['Gains'] += total_profit
                            else:
                                returns_dict[d]['Losses'] += total_profit
                            
                        else:
                            returns_dict[d]['Returns'] = total_profit
                            
                            if total_profit > 0:
                                returns_dict[d]['Gains'] = total_profit
                                returns_dict[d]['Losses'] = 0
                            else:
                                returns_dict[d]['Losses'] = total_profit
                                returns_dict[d]['Gains'] = 0
                                                
                        #print('-----------------')         
                        break #Use break because don't care about orders after sell order
                    
                    else:
                        holdings -= s 
                        print(f'Sell Order: {s} @ {p}')
                        
                        if holdings == 0:
                            ## Reset average after liquidating stock
                            average = 0
                            c = 0
                            print('Sold all holdings')
                        else:
                            print(f'New Holdings Average: {holdings} @ {average}')
                            ## Take away shares from from holding average
                            ## However average stays the same
                            c -= s*average
                x += 1
    
    averages = averages.drop_duplicates(['Trading day', 'Ticker Symbol'], keep='last')
    
    print(f'Gross Returns: {total_returns}')
    net_returns = total_returns - trades['Charges and fees'].sum()
    print(f'Net Returns: {net_returns}')
    
    
    for symbol in all_holdings['Ticker Symbol'].tolist():
                
        df = trades[trades['Ticker Symbol'] == symbol]
        
        df = df.reset_index().drop('index', axis=1)
        
        # formatting float to resolve floating point Arithmetic Issue
        # https://www.codegrepper.com/code-examples/delphi/floating+point+precision+in+python+format
        # https://docs.python.org/3/tutorial/floatingpoint.html
        # could also use the math.isclose() function
        df['Shares'] = df['Shares'].apply(lambda x: float("{:.6f}".format(x))) # Trading 212 only allows fraction of shares up to 6dp 
    
        ## Watchlist
        if df.empty:
            holdings_dict[symbol]['Current Holdings'] = 0
            holdings_dict[symbol]['Current Average'] = 0.0
        
        else:
            print(f'------- {symbol} History -------')
            
            for ii, row in df.iterrows():
                
                ## currently does not take into account fees 
                ## should use total cost column instead later
                ## trading212 doesn't include fees in returns per stock
                
                share_lis = df['Shares'][:ii+1].tolist()
                price_lis = df['Price'][:ii+1].tolist()
                type_lis = df['Type'][:ii+1].tolist()
            
                c = holdings = average = 0 
                #= x
                        
                for s, p, t, in list(zip(share_lis, price_lis, type_lis)):
                    
                    if t == 'Buy':
                        c += s*p
                        holdings += s
                        average = c / holdings
                        print(f'Buy Order: {s} @ {p}')
                        print(f'New Holdings Average: {holdings} @ {average}')
                    
                    else:
        
                        holdings -= s 
                        print(f'Sell Order: {s} @ {p}')
                        
                        if holdings == 0:
                            ## Reset average after liquidating stock
                            average = 0
                            c = 0
                            print('Sold all holdings')
                        else:
                            print(f'New Holdings Average: {holdings} @ {average}')
                            ## Take away shares from from holding average
                            ## However average stays the same
                            c -= s*average
              
            holdings_dict[symbol]['Current Holdings'] = holdings #formatting(holdings)
            holdings_dict[symbol]['Current Average'] = average #formatting(average)
                
            print(f'Holdings Average: {holdings} @ {average}')  
    
    holdings_df = pd.DataFrame.from_dict(holdings_dict, orient='index').reset_index().rename(columns={'index':'Ticker Symbol'})
    returns_df = pd.DataFrame.from_dict(returns_dict, orient='index').reset_index().rename(columns={'index':'Date'})

    returns_df['Date'] = pd.to_datetime(returns_df['Date'], format='%d-%m-%Y')
    
    #returns_df = pd.DataFrame(holdings_dict).transpose().reset_index(level=0).rename(columns={'index':'Ticker Symbol'})
    returns_df.to_sql('returns', engine, if_exists='replace')
    holdings_df.to_sql('holdinigs', engine, if_exists='replace')
    
#returns()




















