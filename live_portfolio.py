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

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

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

live_portfolio.to_sql('holdings', engine, if_exists='replace')

driver.close()
driver.quit()
























