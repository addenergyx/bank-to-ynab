# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 18:54:21 2020

@author: david
"""

from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
from googlefinance import getQuotes
import json
import yfinance as yf
import os
from dotenv import load_dotenv
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from sqlalchemy import create_engine
import re
import difflib
from helpers import get_market, get_yf_symbol

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

def live_portfolio():

    def get_driver():
        options = Options()
        ua = UserAgent()
        userAgent = ua.random
        options.add_argument(f'user-agent={userAgent}')
        
        ## Headless browser - doesn't pop up
        ## A headless browser is a web browser without a graphical user interface.
        #options.add_argument("--headless")  
        
        return webdriver.Chrome(ChromeDriverManager().install(), options=options)
        #return webdriver.Chrome('./chromedriver', options=options)
    
    driver = get_driver()
    
    driver.implicitly_wait(30)
    
    driver.get('https://www.trading212.com/en/login')
    
    driver.find_element_by_id('username-real').send_keys(os.getenv('TRADE_USER'))
    driver.find_element_by_id('pass-real').send_keys(os.getenv('TRADE_PASS'))
    driver.find_element_by_class_name('button-login').click()
    
    driver.find_element_by_xpath('/html/body/div[6]/div[3]/div[2]/div').click()
    
    ## Live results take awhile to load
    time.sleep(10)
    
    elements = driver.find_elements_by_xpath('/html/body/div[5]/div[3]/div/div[2]/div[4]/div')
    
    table = pd.read_html(elements[0].get_attribute('innerHTML'))[0]
    live_portfolio = table.iloc[:,:-2]
    
    headers = driver.find_elements_by_tag_name('thead')
    
    columns = ['Ticker'] + [x.text for x in headers[0].find_elements_by_tag_name('th')[1:9]]
    
    live_portfolio.columns = columns
    
    driver.close()
    driver.quit()
    
    # https://stackoverflow.com/questions/60030570/psycopg2-programmingerror-incomplete-placeholder-without
    # Fix potential SQL injection hole issue, doesn't like '%' in column name
    live_portfolio.rename(columns={'RESULT (%)':'RESULT_PCT'}, inplace=True)  
    
    def remove(string): 
        pattern = re.compile(r'\s+') 
        return re.sub(pattern, '', string) 
    
    cols = ['QUANTITY', 'PRICE', 'CURRENT PRICE', 'MARKET VALUE']
    for col in cols:
        live_portfolio[col] = live_portfolio[col].apply(remove)
        
    live_portfolio[cols] = live_portfolio[cols].apply(pd.to_numeric, errors='coerce')
    
    live_portfolio['Sector'] = ''
    live_portfolio['Industry'] = ''
    live_portfolio['PREV_CLOSE'] = ''
    live_portfolio['YF_TICKER'] = ''
    
    equities = pd.read_sql_table("equities", con=engine, index_col='index')
    companies = equities['COMPANY'].tolist()
    
    def get_sector(r):
    
        # market = get_market(equities[equities['INSTRUMENT'] == r['Ticker']]['ISIN'].values[0], r['Ticker'])[1]
        names = difflib.get_close_matches(r['INSTRUMENT'], companies, n=3, cutoff=0.3)
        #names = difflib.get_close_matches('IAG SA', companies, n=3, cutoff=0.3)
        #market = equities[equities['COMPANY'] == name and equities['INSTRUMENT'] == 'TSLA']  ['MARKET NAME'].values[0]
        
        #print(r['INSTRUMENT']) 
        #ticker = 'NG'
        try:
            market = equities.query('COMPANY==@names and INSTRUMENT==@r.Ticker')['MARKET NAME'].values[0]
        except IndexError:
            market = equities.query('INSTRUMENT==@r.Ticker')['MARKET NAME'].values[0] # Assuming no duplicate tickers
        
        ticker = get_yf_symbol(market, r['Ticker'])
        r['YF_TICKER'] = ticker
        try:
            
            dic = yf.Ticker(ticker).info
            
            r.Sector = dic['sector']
            r.Industry = dic['industry']
            
        except:
            r.Sector = 'Uncategorised'
            r.Industry = 'Uncategorised'
            return r
        return r
    
    live_portfolio = live_portfolio.apply(get_sector, axis=1)
    
    def prev_price(r):
        try:
            r['PREV_CLOSE'] = yf.download(tickers=r['YF_TICKER'], period='2d')['Adj Close'].values[0] #previous close
        except IndexError:
            print(f"Can't find previous price for {r['YF_TICKER']}")
            r['PREV_CLOSE'] = float('NaN')
            pass
        return r
    
    live_portfolio = live_portfolio.apply(prev_price, axis=1)
    
    live_portfolio.to_sql('portfolio', engine, if_exists='replace')

#live_portfolio()


















