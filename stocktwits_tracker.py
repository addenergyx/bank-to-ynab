# -*- coding: utf-8 -*-
"""
Created on Sat Feb 20 13:37:45 2021

@author: david
"""

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
import time
from datetime import date, datetime
import re
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from scraper import get_driver

load_dotenv(verbose=True, override=True)

timestamp = date.today().strftime('%d-%m-%Y')

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

## Google authentication

gauth = GoogleAuth()
#gauth.LocalWebserverAuth()
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    # Authenticate if they're not there
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh them if expired
    gauth.Refresh()
else:
    # Initialize the saved creds
    gauth.Authorize()
gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)

trades = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Last_updated'])

tickers = trades['Ticker Symbol'].drop_duplicates().tolist()

leaderboard = pd.read_sql_table("stocktwits", con=engine, index_col='index')

leaderboard['Date'] = pd.to_datetime(leaderboard['Date'], dayfirst=True)

columns = ['Stock', 'Date', 'Watchers']

#leaderboard = pd.DataFrame(columns=columns)

driver = get_driver()
    
watchers = []

for ticker in tickers:

    try:
        url = 'https://stocktwits.com/symbol/' + ticker
        
        driver.get(url)
        
        watcher = driver.find_element_by_xpath('/html/body/div[3]/div/div/div[3]/div/div/div[1]/div[1]/div/div[1]/div[2]/div[1]/strong').text
        
        def remove(string): 
            pattern = re.compile(r'\s+') 
            return re.sub(pattern, '', string) 
        
        watcher = int(watcher.replace(',', ''))
        
        watchers.append([ticker, timestamp, watcher])
    
    except NoSuchElementException:
        pass

driver.close()
driver.quit()

data = pd.DataFrame(watchers, columns=columns)

def upload_to_google_drive(filename):
    fileList = drive.ListFile({'q': "'14Xi6xKvy8T0NnsbQGJipOVsjskBpwbsb' in parents and trashed=false"}).GetList()
    
    for file in fileList:
        if file['title'] == filename:
            file1 = drive.CreateFile({'id': file['id']})
            file1.Trash()
    
    f = drive.CreateFile({'parents': [{'id': '14Xi6xKvy8T0NnsbQGJipOVsjskBpwbsb'}]}) 
    f.SetContentFile(filename) 
    f.Upload() 
    f = None

df = pd.concat([data, leaderboard], ignore_index=True)

df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

complete_df = df.sort_values(['Stock', 'Date'], ascending=True).drop_duplicates(['Stock','Date'], keep='first')

complete_df['Watchers'] = complete_df['Watchers'].astype(int)

# Use when fixing data
#complete_df = pd.read_csv('stocktwits.csv')

complete_df.to_sql('stocktwits', engine, if_exists='replace')

complete_df.to_csv(f'stocktwits-{timestamp}.csv', index=False)

upload_to_google_drive(f'stocktwits-{timestamp}.csv')
























