# -*- coding: utf-8 -*-
"""
Created on Wed May 27 22:00:41 2020

@author: david
"""
from datetime import datetime, timedelta
import os.path
from scraper import get_div_details
from yahoo_earnings_calendar import YahooEarningsCalendar
from sqlalchemy import create_engine
import pandas as pd
from Google import Create_Service
import sys
from dateutil import parser
import pytz

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

portfolio = pd.read_sql_table("portfolio", con=engine, index_col='index')
#holdings = pd.read_sql_table("holdings", con=engine, index_col='index')

#prev_holdings = list(set(holdings['Ticker Symbol']) - set(portfolio['Ticker']))

## ------------------------- Next Earning Dates ------------------------- ##

yec = YahooEarningsCalendar()

def get_next_earnings(ticker):
    unix = yec.get_next_earnings_date(ticker)
    #yec.get_earnings_of(ticker)
    return datetime.fromtimestamp(unix)

dates = {}

for ticker in list(portfolio['YF_TICKER']):
    try:
        earnings_date = get_next_earnings(ticker)
        if datetime.today() < earnings_date:
            dates[ticker] = earnings_date.strftime('%Y-%m-%d')
            print(f'{ticker}: {get_next_earnings(ticker)}')
        else:
            print(f'{ticker}: Past Earnings {earnings_date}')
    except:
        # Mainly spacs won't have an earnings date
        print(f'{ticker}: No data')

print('')

#dates = {k: dates[k] for k in list(dates)[:2]}

# {x:get_next_earnings(x) for x in list(holdings['YF_TICKER'])}

# from iexfinance.stocks import Stock
# tickr = Stock('AMZN') 
# b = tickr.get_estimates() # should be able to get estimated next earnings report from this
# a = int(b['date'].values[0])
# datetime.fromtimestamp(a)
# datetime.utcfromtimestamp(int(a))

## ------------------------- Log file setup ------------------------- ##

# old_stdout = sys.stdout
# log_file = open("calendar.log","w")
# sys.stdout = log_file

class Tee(object):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)

f = open('calendar.log', 'a')
backup = sys.stdout
sys.stdout = Tee(sys.stdout, f)

now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00')

print(f'## ------------------------- {now} ------------------------- ##')
print('')

## ------------------------- Google Calendar ------------------------- ##

CLIENT_SECRET_FILE = 'Client_Secret.json'
API_NAME = 'calendar'
API_VERSION = 'v3'

# If modifying these scopes, delete the file token_calendar_v3.pickle and let script recreate one 
SCOPES = ['https://www.googleapis.com/auth/calendar']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

response = service.calendarList().list().execute()
#pprint(response)

calendars = response.get('items')

stock_calendar = next((item for item in calendars if item['summary'] == 'Stocks'), None)

calendar_id_stocks = stock_calendar['id']

#colours = service.colors().get().execute()

def create_body(ticker, date):
    return {
      'summary': f'{ticker} Earnings',
      'description': f'https://uk.finance.yahoo.com/quote/{ticker}/',
      'start': {
        'date': date,
        'timeZone': 'Europe/London',
      },
      'end': {
        'date': date,
        'timeZone': 'Europe/London',
      },
      'colorId' : 0,
      'reminders': {
        'useDefault': True,
        # 'useDefault': False,
        # 'overrides': [
        #   {'method': 'email', 'minutes': 24 * 60},
        #   {'method': 'popup', 'minutes': 24 * 60},
        #   {'method': 'email', 'minutes': 48 * 60},
        #   {'method': 'popup', 'minutes': 48 * 60},
        #   #{'method': 'email', 'minutes': 168 * 60},
        #   {'method': 'popup', 'minutes': 168 * 60},
        # ],
      },
    } 

# Gets all future events in stocks calendar 
# events = service.events().list(
#     calendarId=calendar_id_stocks,
#     singleEvents=True,
#     orderBy='startTime',
#     timeMin=timemin,
# ).execute()

def get_events(timeMin=now):
    return service.events().list(
        calendarId=calendar_id_stocks,
        singleEvents=True,
        orderBy='startTime',
        timeMin=now,
    ).execute()

events = get_events()

# key = 'TSLA'
# value = '2021-02-03'

# https://www.youtube.com/playlist?list=PL3JVwFmb_BnTO_sppfTh3VkPhfDWRY5on
for key, value in dates.items():
    
    # value = '2021-02-03'
    counter = 0
    num = len(events['items'])
    
    # # TODO: Might need to update events after each ticker
    # events = service.events().list(
    #     calendarId=calendar_id_stocks,
    #     singleEvents=True,
    #     orderBy='startTime',
    #     timeMin=datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'),
    # ).execute()
    
    for event in events['items']:
        
        if event['summary'] == f'{key} Earnings':
            
            if event['start']['date'] != value:
                eventId = event['id']
                
                # Update existing event
                service.events().update(
                    calendarId=calendar_id_stocks,
                    eventId=eventId,
                    body=create_body(key, value),
                ).execute()
                print(f'Updating event {key}: {value}')
            break
        
        else:
            counter += 1
            #print('Do Nothing')
    
    if counter == num:
        # Create new event
        response = service.events().insert(
            calendarId=calendar_id_stocks,
            sendNotifications=True,
            sendUpdates='none',
            body=create_body(key, value)
        ).execute()
        print(f'Creating event {key}: {value}')
    # else:
    #     print(f'{key} already exists')

## ------------------------- Three day rule events ------------------------- ##

# If company misses earnings stock should drop for 3 trading days

# def create_bodyx(ticker, date):
#     #date = '2021-02-05'
#     return {
#       'summary': f'{ticker} Missed Earnings',
#       'description': 'Three day rule',
#       'start': {
#         'date': date,
#         'timeZone': 'Europe/London',
#       },
#       'end': {
#         'date': date,
#         'timeZone': 'Europe/London',
#       },
#       'colorId' : 8,
#       'reminders': {
#         'useDefault': False,
#         'overrides': [
#           {'method': 'email', 'minutes': 24 * 60},
#           {'method': 'popup', 'minutes': 24 * 60},
#           {'method': 'email', 'minutes': 48 * 60},
#         ],
#       },
#     } 

# timemin = datetime.now() - timedelta(days=10)
# timemin = timemin.strftime('%Y-%m-%dT%H:%M:%S-00:00')
# events = get_events(timeMin=timemin)

# for ticker in list(portfolio['YF_TICKER']):

# #for ticker in ['TSLA', 'AAPL', 'MTCH', 'MPW']:
#     #print(ticker)
#     a = yec.get_earnings_of(ticker)
#     counter = 0
#     num = len(events['items'])
    
#     if a:
    
#         for x in a:
#             if x['epsactual'] is not None:
#                 break
                
#         if x['epsactual'] is None or x['epsestimate'] is None:
#             continue
#         elif x['epsactual'] < x['epsestimate']:
#             #print(f"{x['ticker']} missed earnings {parser.parse(x['startdatetime']).strftime('%Y-%m-%d')}")
#             # x['startdatetime']
#             # x['timeZoneShortName']
            
#             for event in events['items']:
#                 #print(event['summary'])
#                 if event['summary'] == f'{ticker} Missed Earnings':
#                     #print(f"{ticker} event already exists")
#                     break
#                 else:
#                     counter += 1
#                     #print('Do Nothing')
            
#             if counter == num:
                
#                 utc=pytz.UTC
#                 #TODO: may need to change this line as 'startdatetime' wouldn't be a day in the future
#                 q = datetime.now() - timedelta(days=7) 
#                 if parser.parse(x['startdatetime']).replace(tzinfo=utc) > q.replace(tzinfo=utc):
                
#                     date = parser.parse(x['startdatetime']) + timedelta(days=3) 
#                     date = date.strftime('%Y-%m-%d')
                    
#                     # Create new event
#                     response = service.events().insert(
#                         calendarId=calendar_id_stocks,
#                         sendNotifications=True,
#                         sendUpdates='none',
#                         body=create_bodyx(ticker, date)
#                     ).execute()
#                     print(f'Creating missed earnings event {ticker}')  

print('')
sys.stdout = backup
f.close()  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    