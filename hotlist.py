# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 20:56:03 2020

@author: david
"""

# import requests
# from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
#from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
from datetime import date, datetime
from webdriver_manager.chrome import ChromeDriverManager
import re

## Trading 212 hot list
## On 2nd November Trading 212 added a popularity tracker to their site
## Can You Predict Stock Price Movements With Users’ Behaviour data?
## T212 doesn't store historical data so will be scrapping site daily and storing the results in a csv
## Trading 212 uses javascript to load the data so have to use selenium instead of beautifulsoup

timestamp = date.today().strftime('%d-%m-%Y')

## Using Long table as it's more flexible for this dataset
## Improve: use database instead of csv
leaderboard = pd.read_csv('leaderboard.csv', parse_dates=[4], dayfirst=True) # Date format changes for some observations when reading csv unsure why
risers = pd.read_csv('risers.csv')
fallers = pd.read_csv('fallers.csv')

columns = ['Stock', 'Position', 'Start', 'End', 'Date', 'User_change', 'Percentage_change', 'Last_updated']

# ase = leaderboard[leaderboard['Date'] == '11-11-2020'].reset_index(drop=True)
# ase['Position'] = list(ase.index+1)

## For webapp
overall_leaderboard = leaderboard.drop_duplicates('Stock', keep='first').reset_index(drop=True)
overall_leaderboard['Position'] = list(overall_leaderboard.index+1)

## ------------------------- Selenium Setup ------------------------- ##

def get_driver():
    options = Options()
    ua = UserAgent()
    userAgent = ua.random
    options.add_argument(f'user-agent={userAgent}')
    
    ## Headless browser - doesn't pop up
    ## A headless browser is a web browser without a graphical user interface.
    #options.add_argument("--headless")  
    
    return webdriver.Chrome(ChromeDriverManager().install(), options=options) # automatically use the correct chromedriver by using the webdrive-manager
    #return webdriver.Chrome('./chromedriver', options=options)

driver = get_driver()

## ------------------------- Leaderboard ------------------------- ##

daily_hotlist = []

driver.get(f'https://www.trading212.com/en/hotlist')

time.sleep(5) # Pause for page to load

elements = driver.find_elements_by_class_name("pt-popularity-content-item")

def get_last_update(update):
    match = re.search(r'\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}', update)
    last_update = datetime.strptime(match.group(), '%d/%m/%Y, %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
    return last_update

# Get date from string
update = driver.find_element_by_class_name("pt-footer-notice").text
last_update = get_last_update(update)

for stock in elements:
    daily_hotlist.append([stock.find_element_by_class_name('pt-name').text, 
            stock.find_element_by_class_name('pt-number').text, 
            stock.find_element_by_class_name('pt-holders-count').text, 
            timestamp,
            last_update])

## Direct correlation between position and user count so should remove position for model
data = pd.DataFrame(daily_hotlist, columns=['Stock', 'Position', 'User_count', 'Date', 'Last_updated'])
data['User_count'] = data['User_count'].str.replace(',', '').astype(float)

df = pd.concat([data, leaderboard], ignore_index=True)

## This script will run several times a day to get as much data as possible. 
## Because positions throughout the day will keep changing. For example when US or UK markets open stocks in their
## region would naturally climb up the table.

#To drop duplicates based on multiple columns:
#https://stackoverflow.com/questions/12497402/python-pandas-remove-duplicates-by-columns-a-keeping-the-row-with-the-highest
complete_df = df.sort_values('User_count', ascending=False).drop_duplicates(['Stock','Date'], keep='first').reset_index(drop=True) #.sort_index()

## Fix positions column

#complete_df['Last_updated'] = pd.to_datetime(complete_df.Last_updated)
complete_df['Date'] = pd.to_datetime(complete_df.Date)
complete_df = complete_df.sort_values(['Date', 'User_count'], ascending=[True, False])

comp = pd.DataFrame()

for d in complete_df['Date'].unique():
    temp_df = complete_df[complete_df['Date'] == d].reset_index(drop=True)
    temp_df['Position'] = list(temp_df.index+1)
    comp = comp.append(temp_df, ignore_index=True)

complete_df = comp.copy()
complete_df['Date'] = complete_df['Date'].dt.strftime('%d/%m/%Y')
complete_df.to_csv('leaderboard.csv', index=False)

## Position in dataset
# complete_df = complete_df.sort_values('User_count', ascending=False)
## Reset positions, use list() so it's int instead of string
# complete_df['Position'] = list(complete_df.index+1)

## ------------------------- Daily Risers/Fallers ------------------------- ##

def user_data(xpath, file, historical_df):
    daily = []
    
    driver.find_element_by_xpath(xpath).click()
    
    time.sleep(5) # Pause for page to load
    
    update = driver.find_element_by_class_name("pt-footer-notice").text
    last_update = get_last_update(update)
    
    elements = driver.find_elements_by_class_name("pt-popularity-content-item")
    
    for stock in elements[1:]:
        daily.append([stock.find_element_by_class_name('pt-name').text, 
                stock.find_element_by_class_name('pt-number').text, 
                stock.find_element_by_class_name('pt-change').text,
                stock.find_element_by_class_name('pt-start').text,
                stock.find_element_by_class_name('pt-end').text,
                timestamp,
                last_update])
    
    data = pd.DataFrame(daily, columns=['Stock', 'Position', 'Change','Start', 'End', 'Date', 'Last_updated'])
    
    data[['User_change','Percentage_change']] = data['Change'].str.split(' ', expand=True)
    data = data.drop('Change', 1) # inplace=True not working
    data['Percentage_change'] = data['Percentage_change'].str.strip('()').str.strip('%').astype(float) # Remove brackets
    data['User_change'] = data['User_change'].str.replace(',', '').astype(float)
    data['Start'] = data['Start'].str.replace(',', '').astype(float)
    data['End'] = data['End'].str.replace(',', '').astype(float)
    
    data = data[columns]
    
    df = pd.concat([data, historical_df], ignore_index=True)
    
    ## To fix fallers position column make column abs then times by -1 after reorder
    
    complete_df = df.sort_values('User_change', ascending=False).drop_duplicates(['Stock','Date'], keep='first').reset_index(drop=True)
    
    complete_df['User_change'] = complete_df['User_change'].abs()
    
    complete_df['Date'] = pd.to_datetime(complete_df.Date)
    
    complete_df = complete_df.sort_values(['Date', 'User_change'], ascending=[True, False])

    comp = pd.DataFrame()
    
    for d in complete_df['Date'].unique():
        temp_df = complete_df[complete_df['Date'] == d].reset_index(drop=True)
        temp_df['Position'] = list(temp_df.index+1)
        comp = comp.append(temp_df, ignore_index=True)
    
    complete_df = comp.copy()
    
    #complete_df['User_change'] = complete_df['User_change'] * -1
    complete_df['Date'] = complete_df['Date'].dt.strftime('%d/%m/%Y')
    complete_df.to_csv(file, index=False)
    
    return complete_df

risers_df = user_data("/html/body/div[1]/section[2]/div/div/div[1]/div/div[2]", 'risers.csv', risers)

fallers_df = user_data("/html/body/div[1]/section[2]/div/div/div[1]/div/div[3]", 'fallers.csv', fallers)

## ------------------------- Selenium Shutdown ------------------------- ##

driver.close()
driver.quit()


