# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 17:52:14 2021

@author: david
"""

import os
from dotenv import load_dotenv
import yfinance as yf
from datetime import datetime, time
from sqlalchemy import create_engine
from iexfinance.stocks import Stock
from scraper import getPremarketChange, get_driver
from helpers import get_holdings
import time as t
import schedule

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

def day_chart():
        
    # print('start')
    start_time = t.time()
    
    if time(hour=9, minute=0) < datetime.now().time() < time(hour=14, minute=30) or time(hour=21) < datetime.now().time() < time(hour=22):
        driver = get_driver(
            headless=True
            #proxy=True
            )
    
    def current_price(r):
        #print(r['YF_TICKER'])
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
    
    holdings.to_sql('day_chart', engine, if_exists='replace')
    
    end_time = t.time()
    # print(end_time-start_time)
    # print('end')

def job():
    day_chart()
                
schedule.every(30).seconds.do(job)

while True:
    if datetime.now().time() < time(hour=19, minute=8):
        schedule.run_pending()
        t.sleep(1)
    else:
        break
    
    
    
    
    
    
    
    