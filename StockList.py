# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 17:07:13 2020

@author: david
"""
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import os
from sqlalchemy import create_engine

## Scraping Stocks in Trading212 site ##
## Need this to put the right trailing value for yahoo finance (i.e .L/.MI)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

## Merging stored stock list with scraped stock list to account for stocks removed from Trading 212 or company name changes
historical_df = pd.read_csv('stock_list.csv')

url = "https://www.trading212.com/en/Trade-Equities"

headers = {
    'User-Agent': 'My User Agent 1.0',
}

r = requests.get(url, headers=headers)

#print(r.content) 
soup = BeautifulSoup(r.content, 'html5lib')

table = soup.find('div', attrs = {'id':'all-equities'})

instruments = []
for row in table.findAll('div', id=lambda x: x and x.startswith('equity-row-')):
    instrument = {}
    instrument['INSTRUMENT'] = row.find('div', attrs = {'data-label':'Instrument'}).text
    instrument['COMPANY'] = row.find('div', attrs = {'data-label':'Company'}).text
    # instrument['CURRENCY CODE'] = row.find('div', attrs = {'data-label':'Currency code'}).text
    instrument['ISIN'] = row.find('div', attrs = {'data-label':'ISIN'}).text
    # instrument['MIN TRADED QUANTITY'] = row.find('div', attrs = {'data-label':'Min traded quantity'}).text
    instrument['MARKET NAME'] = row.find('div', attrs = {'data-label':'Market name'}).text
    # instrument['MARKET HOURS (GMT)'] = row.find('div', attrs = {'data-label':'Market hours (GMT)'}).text
    instruments.append(instrument)
 
all_212_equities = pd.DataFrame(instruments)

all_212_equities = pd.concat([all_212_equities, historical_df], ignore_index=True)

all_212_equities.drop_duplicates(['INSTRUMENT','COMPANY'], keep='first', inplace=True)

all_212_equities.to_csv('stock_list.csv', index=False)

all_212_equities.to_sql('equities', engine, if_exists='replace')