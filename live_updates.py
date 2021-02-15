# -*- coding: utf-8 -*-
"""
Created on Wed Feb  3 11:36:49 2021

@author: david
"""

import os
import pandas as pd
from dotenv import load_dotenv
from pandas_datareader import data as web
import yfinance as yf
from datetime import datetime, timedelta, time
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go
from pytrends.request import TrendReq
from sqlalchemy import create_engine
from pytrends import dailydata
from helpers import get_buy_sell, get_yf_symbol, time_frame_returns
from forex_python.converter import CurrencyRates
from plotly.subplots import make_subplots
from iexfinance.stocks import Stock
from scraper import getPremarketChange, get_driver
from fake_useragent import UserAgent
#import time as t

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

def get_holdings():
    holdings = pd.read_sql_table("portfolio", con=engine, index_col='index')
    
    # driver = get_driver(#headless=True
    #     )
    # driver.implicitly_wait(20)
    
    # holdings = holdings.apply(current_price, axis=1)
    # driver.close()
    # driver.quit()
    
    # holdings.dropna(axis=0, inplace=True)
    
    # Recent ticker change due to merger, Yahoo finance pulls wrong data, should be fixed later
    #holdings = holdings[holdings['Ticker'] != 'UWMC']
    
    holdings['PREV_CLOSE'] = holdings['PREV_CLOSE'].astype('float')
    #print('got holdings')
    return holdings

def day_chart():
        
    if time(hour=9, minute=0) < datetime.now().time() < time(hour=14, minute=30) or time(hour=21) < datetime.now().time() < time(hour=22):
        driver = get_driver(
            headless=True
            #proxy=True
            )
    
    def current_price(r):
        print(r['YF_TICKER'])
        if time(hour=9, minute=0) < datetime.now().time() < time(hour=14, minute=30) or time(hour=21) < datetime.now().time() < time(hour=22):
            if r['YF_TICKER'].find('.') == -1:
                try:
                    # Use IEX, only works with US (NYSE) Stocks
                    tickr = Stock(r['YF_TICKER']) 
                    #tickr = Stock('TSLA')
                    data = tickr.get_quote()
                    
                    if data['primaryExchange'].values[0].find('NASDAQ') == 0:
                        r['CURRENT_PRICE'] = getPremarketChange(r['YF_TICKER'], driver)
                    else:             
                        # a = tickr.get_price_target()
                        # b = tickr.get_estimates()
                        latestPrice = data['latestPrice'].values[0]
                        extendedPrice = data['extendedPrice'].values[0]
                        #iexRealtimePrice = data['iexRealtimePrice'].values[0]
                        
                        # Only works with non nasdaq stocks due to new regulations 
                        #https://intercom.help/iexcloud/en/articles/3210401-how-do-i-get-nasdaq-listed-stock-data-utp-data-on-iex-cloud
                        r['CURRENT_PRICE'] = latestPrice if extendedPrice is None else extendedPrice
                    return r
    
                except: 
                    try:
                        r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
                        return r
                    except:
                        r['CURRENT_PRICE'] = float('NaN')
                        return r
            else:
                try:
                    r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
                    return r
                except:
                    r['CURRENT_PRICE'] = float('NaN')
                    return r
        else:
            try:
                r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
            except:
                r['CURRENT_PRICE'] = float('NaN')
            return r
        
    holdings = get_holdings()
    holdings = holdings.apply(current_price, axis=1)
    
    if 'driver' in locals():
        driver.close()
        driver.quit()
    
    holdings['PCT'] = (holdings['CURRENT_PRICE'] - holdings['PREV_CLOSE']) / abs(holdings['PREV_CLOSE']) *100
    holdings['PCT'] = holdings['PCT'].round(2)    
    
    # Yahoo finance pulls wrong data, should be fixed later
    holdings = holdings[holdings['Ticker'] != 'IITU']
    holdings = holdings[holdings['Ticker'] != '3CRM']
    
    fig = px.treemap(holdings, path=['Sector', 'Industry', 'Ticker'], values='MARKET_VALUE', color='PCT',
                     color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=[-20,20], 
                     #hover_data=['Ticker', 'MARKET VALUE', 'PCT']
                     )
        
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        transition={
                            'duration': 500,
                            'easing': 'cubic-in-out',
                        }
                      )
    fig.update_layout(coloraxis_showscale=False)
    fig.data[0].hovertemplate = '%{label}<br>%{color}%<br>£%{value}'
    
    print('launch day map')

    #fig.data[0].textinfo = 'label+text+percent entry+percent parent+value'
    #plot(fig)
    
    return fig

def return_map():
    
    if time(hour=9, minute=0) < datetime.now().time() < time(hour=14, minute=30) or time(hour=21) < datetime.now().time() < time(hour=22):
        driver = get_driver(#
            headless=True
            #proxy=True
            )
    
    holdings = get_holdings()

    def current_price(r):
        print(r['YF_TICKER'])
        if time(hour=9, minute=0) < datetime.now().time() < time(hour=14, minute=30) or time(hour=21) < datetime.now().time() < time(hour=22):
            if r['YF_TICKER'].find('.') == -1:
                try:
                    # Use IEX, only works with US (NYSE) Stocks
                    tickr = Stock(r['YF_TICKER']) 
                    #tickr = Stock('TSLA')
                    data = tickr.get_quote()
                    
                    if data['primaryExchange'].values[0].find('NASDAQ') == 0:
                        r['CURRENT_PRICE'] = getPremarketChange(r['YF_TICKER'], driver)
                    else:             
                        # a = tickr.get_price_target()
                        # b = tickr.get_estimates()
                        latestPrice = data['latestPrice'].values[0]
                        extendedPrice = data['extendedPrice'].values[0]
                        #iexRealtimePrice = data['iexRealtimePrice'].values[0]
                        
                        # Only works with non nasdaq stocks due to new regulations 
                        #https://intercom.help/iexcloud/en/articles/3210401-how-do-i-get-nasdaq-listed-stock-data-utp-data-on-iex-cloud
                        r['CURRENT_PRICE'] = latestPrice if extendedPrice is None else extendedPrice
                    return r
    
                except: 
                    try:
                        r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
                        return r
                    except:
                        r['CURRENT_PRICE'] = float('NaN')
                        return r
            else:
                try:
                    r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
                    return r
                except:
                    r['CURRENT_PRICE'] = float('NaN')
                    return r
        else:
            try:
                r['CURRENT_PRICE'] = yf.download(tickers=r['YF_TICKER'], period='1m', progress=False)['Close'].values[0]
            except:
                r['CURRENT_PRICE'] = float('NaN')
            return r
    
    holdings = holdings.apply(current_price, axis=1)
    
    if 'driver' in locals():
        driver.close()
        driver.quit()
    
    holdings.dropna(axis=0, inplace=True)
    holdings['Ri'] = (holdings['CURRENT_PRICE'] - holdings['PRICE']) / abs(holdings['PRICE']) *100 # May be slightly off due to fx
    fig = px.treemap(holdings, path=['Sector', 'Industry', 'Ticker'], values='MARKET_VALUE', color='Ri',
                     color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=[-30,30])
    
    fig.update_layout(    
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    #https://plotly.com/python/colorscales/#setting-the-midpoint-of-a-color-range-for-a-diverging-color-scale
    fig.update_layout(coloraxis_showscale=False)
    fig.data[0].hovertemplate = '%{label}<br>%{color}%<br>£%{value}'
    print('launch returns map')
    #plot(fig)
    return fig

# import time as t

# for x in range(4):
#     start = t.time()
#     day_chart()
#     end = t.time()
#     print(end - start)
#     print(x)
# start = t.time()
# return_map() 
# end = t.time()
# print(end - start)

# No proxy
# Day 97.88992285728455
# Returns 103.6159348487854

# With proxy
# Day 542.8661546707153
# Returns 310.96697425842285

    
    
    
    
    
    
    
    
    