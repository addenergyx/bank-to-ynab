# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 18:28:13 2020

@author: david
"""

from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import os
from dotenv import load_dotenv
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
import os
from sqlalchemy import create_engine

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

def get_tickers():
    
    driver = get_driver()
    
    driver.implicitly_wait(20)        
    
    driver.maximize_window()
    
    driver.get('https://www.trading212.com/en/login')
    
    ## Login
    driver.find_element_by_id('username-real').send_keys(os.getenv('PRAC_TRADE_USER'))
    driver.find_element_by_id('pass-real').send_keys(os.getenv('PRAC_TRADE_PASS'))
    driver.find_element_by_class_name('button-login').click()
    
    driver.find_element_by_xpath('/html/body/div[4]/div[4]/div/div[1]/span').click()
    
    aa_dict = {}
    
    leaderboard = pd.read_csv('leaderboard.csv', parse_dates=['Date', 'Last_updated'], dayfirst=True)
    
    stocks = list(leaderboard['Stock'].unique())
    
    for stock in stocks:
        ## Loop
        driver.find_element_by_class_name('search-input').clear()
        driver.find_element_by_class_name('search-input').send_keys(stock)
        
        #elements = driver.find_elements_by_xpath('/html/body/div[7]/div[2]/div[2]/div[3]/div[3]/div') # For real trading account
        elements = driver.find_elements_by_xpath('/html/body/div[8]/div[2]/div[2]/div[3]/div[3]')
        
        ## First div in row should be first row
        row = elements[0].find_element_by_tag_name('div')
        
        # row.find_element_by_class_name('ticker').text
        # row.find_element_by_class_name('market-name').text
        
        print(row.find_element_by_class_name('has-ellipsed-text').text)
        
        name = row.find_element_by_class_name('has-ellipsed-text').text
        ticker = re.search(r'\((.*?)\)', name).group(1)
            
        aa_dict[stock] = {'ticker':ticker,
                              'market':row.find_element_by_class_name('market-name').text}
    
    driver.close()
    driver.quit()
    
    df = pd.DataFrame.from_dict(aa_dict, orient='index').reset_index(drop=False).rename(columns={'index':'Company'})
    
    df.to_csv('leaderboard_tickers.csv')
        
    df.to_sql('leaderboard_tickers', engine, if_exists='replace')
    
    return aa_dict

get_tickers()



































