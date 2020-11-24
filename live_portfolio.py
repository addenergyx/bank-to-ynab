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

load_dotenv(verbose=True, override=True)

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

driver.implicitly_wait(10)

driver.get('https://www.trading212.com/en/login')

driver.find_element_by_id('username-real').send_keys(os.getenv('TRADE_USER'))
driver.find_element_by_id('pass-real').send_keys(os.getenv('TRADE_PASS'))
driver.find_element_by_xpath('/html/body/div[1]/section[2]/div/div[2]/div/form/input[6]').click()

driver.find_element_by_xpath('/html/body/div[6]/div[3]/div[2]/div').click()

elements = driver.find_elements_by_xpath('/html/body/div[5]/div[3]/div/div[2]/div[4]/div')

table = pd.read_html(elements[0].get_attribute('innerHTML'))[0]
live_portfolio = table.iloc[:,:-2]

headers = driver.find_elements_by_tag_name('thead')

columns = ['Ticker'] + [x.text for x in headers[0].find_elements_by_tag_name('th')[1:9]]

live_portfolio.columns = columns
    
driver.close()
driver.quit()

































