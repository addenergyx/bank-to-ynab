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
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
from datetime import date, datetime
from webdriver_manager.chrome import ChromeDriverManager
import re
#import os.path

## Trading 212 hot list
## On 2nd November Trading 212 added a popularity tracker to their site
## Can You Predict Stock Price Movements With Users’ Behavior?
## T212 doesn't store historical data so will be scrapping site daily and storing the results in a csv
## Trading 212 uses javascript to load the data so have to use selenium instead of beautifulsoup

timestamp = date.today().strftime('%d-%m-%Y')

## Using Long table as it's more flexible for this dataset
## Improve: use database instead of csv
leaderboard = pd.read_csv('leaderboard.csv', parse_dates=[4], dayfirst=True) # Date format changes for some observations when reading csv unsure why
risers = pd.read_csv('risers.csv')
fallers = pd.read_csv('fallers.csv')

columns = ['Stock', 'Position', 'Start', 'End', 'Date', 'User_change', 'Percentage_change', 'Last_updated']

# if os.path.isfile(f'leaderboard_{timestamp}.csv'):
#     leaderboard = pd.read_csv(f'leaderboard_{timestamp}.csv')
# else:
#     leaderboard = pd.DataFrame(columns=['Stock', 'Position', 'User_count', 'Date', 'Last_updated'])

# if os.path.isfile(f'leaderboard_{timestamp}.csv'):
#     risers = pd.read_csv(f'risers_{timestamp}.csv')
# else:
#     risers = pd.DataFrame(columns=['Stock', 'Position', 'Start', 'End', 'Date', 'User_change', 'Percentage_change', 'Last_updated'])
    
# if os.path.isfile(f'fallers_{timestamp}.csv'):
#     fallers = pd.read_csv(f'fallers_{timestamp}.csv')
# else:
#     fallers = pd.DataFrame(columns=['Stock', 'Position', 'Start', 'End', 'Date', 'User_change', 'Percentage_change', 'Last_updated'])

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

daily_hotlist = []

driver.get(f'https://www.trading212.com/en/hotlist')

time.sleep(5) # Pause for page to load

a = driver.find_elements_by_class_name("pt-popularity-content-item")

def get_last_update(update):
    match = re.search(r'\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}', update)
    last_update = datetime.strptime(match.group(), '%d/%m/%Y, %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S')
    return last_update

# Get date from string
update = driver.find_element_by_class_name("pt-footer-notice").text
last_update = get_last_update(update)

for stock in a:
    daily_hotlist.append([stock.find_element_by_class_name('pt-name').text, 
            stock.find_element_by_class_name('pt-number').text, 
            stock.find_element_by_class_name('pt-holders-count').text, 
            timestamp,
            last_update])

## Direct correlation between position and user count so should remove position for model
data = pd.DataFrame(daily_hotlist, columns=['Stock', 'Position', 'User_count', 'Date', 'Last_updated'])
#data['Last_updated'] = pd.to_datetime(data['Last_updated'])
data['User_count'] = data['User_count'].str.replace(',', '').astype(float)

df = pd.concat([data, leaderboard], ignore_index=True)

## This script will run several times a day to get as much data as possible. 
## Because positions throughout the day will keep changing. For example when US or UK markets open stocks in their
## region would naturally climb up the table.

#To drop duplicates based on multiple columns:
#https://stackoverflow.com/questions/12497402/python-pandas-remove-duplicates-by-columns-a-keeping-the-row-with-the-highest
complete_df = df.sort_values('User_count', ascending=False).drop_duplicates(['Stock','Date'], keep='first').reset_index(drop=True) #.sort_index()

## Reset positions, use list() so it's int instead of string
complete_df['Position'] = list(complete_df.index+1)
complete_df.to_csv('leaderboard.csv', index=False)

## This script should only run once a day as a cron job but if ran more then once this will pervent duplicate entries
# if not leaderboard[-100:].equals(data):
#     leaderboard = pd.concat([leaderboard, data])
#     leaderboard.to_csv('leaderboard.csv', index=False)

## ------------------------- Risers/Fallers ------------------------- ##

def user_data(xpath, file, historical_df):
    daily = []
    
    driver.find_element_by_xpath(xpath).click()
    
    time.sleep(5) # Pause for page to load
    
    update = driver.find_element_by_class_name("pt-footer-notice").text
    last_update = get_last_update(update)
    
    a = driver.find_elements_by_class_name("pt-popularity-content-item")
    
    for stock in a[1:]:
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
    
    complete_df = df.sort_values('User_change', ascending=False).drop_duplicates(['Stock','Date'], keep='first').reset_index(drop=True) #.sort_index()
    
    complete_df['Position'] = list(complete_df.index+1)
    complete_df.to_csv(file, index=False)
    
    return complete_df

risers_df = user_data("/html/body/div[1]/section[2]/div/div/div[1]/div/div[2]", 'risers.csv', risers)

fallers_df = user_data("/html/body/div[1]/section[2]/div/div/div[1]/div/div[3]", 'fallers.csv', fallers)

## ------------------------- Fallers ------------------------- ##

# daily_fallers = []

# driver.find_element_by_xpath("/html/body/div[1]/section[2]/div/div/div[1]/div/div[3]").click()

# time.sleep(5) # Pause for page to load

# update = driver.find_element_by_class_name("pt-footer-notice").text
# last_update = get_last_update(update)

# a = driver.find_elements_by_class_name("pt-popularity-content-item")

# for stock in a[1:]:
#     daily_fallers.append([stock.find_element_by_class_name('pt-name').text, 
#             stock.find_element_by_class_name('pt-number').text, 
#             stock.find_element_by_class_name('pt-change').text,
#             stock.find_element_by_class_name('pt-start').text,
#             stock.find_element_by_class_name('pt-end').text,
#             timestamp,
#             last_update])

# data = pd.DataFrame(daily_fallers)

# data[['User_change','Percentage_change']] = data[2].str.split(' ', expand=True)
# data = data.drop(2, 1) # inplace=True not working
# data['Percentage_change'] = data['Percentage_change'].str.strip('()') # Remove brackets
# data.columns = fallers.columns
# data['Start'] = data['Start'].str.replace(',', '').astype(float)
# data['End'] = data['End'].str.replace(',', '').astype(float)

# if not fallers[-100:].equals(data):
#     fallers = pd.concat([fallers, data])
#     fallers.to_csv('fallers.csv', index=False)


driver.close()
driver.quit()


