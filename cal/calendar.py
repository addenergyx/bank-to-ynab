# -*- coding: utf-8 -*-
"""
Created on Wed May 27 22:00:41 2020

@author: david
"""
from datetime import datetime, timedelta
import os.path
# from scraper import get_div_details
# from yahoo_earnings_calendar import YahooEarningsCalendar
from sqlalchemy import create_engine
import pandas as pd
from Google import Create_Service
import sys
from dateutil import parser
import pytz
from google_calendar import create_event, update_event, delete_event, get_events, active
import yahoo_fin.stock_info as si
from dotenv import load_dotenv

load_dotenv(verbose=True, override=True)

STOCKS_CALENDAR_ID = os.getenv('STOCKS_CALENDAR_ID')

# db_URI = os.getenv('AWS_DATABASE_URL')

# db_URI = os.getenv('ElephantSQL_DATABASE_URL')

# engine = create_engine(db_URI)

# portfolio = pd.read_sql_table("portfolio", con=engine, index_col='index')
#holdings = pd.read_sql_table("holdings", con=engine, index_col='index')

#prev_holdings = list(set(holdings['Ticker Symbol']) - set(portfolio['Ticker']))

## ------------------------- Next Earning Dates ------------------------- ##

dates = {}

# for ticker in list(portfolio['YF_TICKER']):
for ticker in ['AAPL', 'TSLA', 'MSFT', 'NIO']:
    try:
        earnings_date = si.get_next_earnings_date(ticker)
        if datetime.today() < earnings_date:
            dates[ticker] = earnings_date.strftime('%Y-%m-%d')
            print(f'{ticker}: {earnings_date}')
        else:
            print(f'{ticker}: Past Earnings {earnings_date}')
    except Exception as e:
        # Mainly spacs won't have an earnings date
        print(f'{ticker}: No data {e}')

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

### uncomment ###

# class Tee(object):
#     def __init__(self, *files):
#         self.files = files
#     def write(self, obj):
#         for f in self.files:
#             f.write(obj)

# f = open('calendar.log', 'a')
# backup = sys.stdout
# sys.stdout = Tee(sys.stdout, f)

now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00')

print(f'## ------------------------- {now} ------------------------- ##')
print('')

## ------------------------- Google Calendar ------------------------- ##

# Gets all future events in stocks calendar 
# events = service.events().list(
#     calendarId=calendar_id_stocks,
#     singleEvents=True,
#     orderBy='startTime',
#     timeMin=timemin,
# ).execute()

events = get_events(calendar_id=STOCKS_CALENDAR_ID)

# key = 'TSLA'
# value = '2021-02-03'

# https://www.youtube.com/playlist?list=PL3JVwFmb_BnTO_sppfTh3VkPhfDWRY5on
for key, value in dates.items():
    
    # value = '2021-02-03'
    counter = 0
    num = len(events)
    
    # # TODO: Might need to update events after each ticker
    # events = service.events().list(
    #     calendarId=calendar_id_stocks,
    #     singleEvents=True,
    #     orderBy='startTime',
    #     timeMin=datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'),
    # ).execute()
    
    title = f'{key} Earnings'
    
    for event in events:
        
        if event['summary'] == f'{key} Earnings':
            
            if event['start']['date'] != value:
                event_Id = event['id']
                
                # Update existing event
                update_event(title, value, value, event_id=event_id, calendar_id=calendar_id, colour=0)

                print(f'Updating event {key}: {value}')
            break
        
        else:
            counter += 1
            #print('Do Nothing')
    
    if counter == num:
        # Create new event
        create_event(title, value, value, calendar_id=calendar_id, colour=0)

        # response = service.events().insert(
        #     calendarId=calendar_id_stocks,
        #     sendNotifications=True,
        #     sendUpdates='none',
        #     body=create_body(key, value)
        # ).execute()
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
    
    timemin = datetime.now() - timedelta(days=10)
    timemin = timemin.strftime('%Y-%m-%dT%H:%M:%S-00:00')
    events = get_events(time_min=timemin, calendar_id=calendar_id)
    
    # for ticker in list(portfolio['YF_TICKER']):
    
    #print(ticker)
    earnings_df = si.get_earnings(ticker)
    counter = 0
    num = len(events)
    
    now = datetime.now()
    
    quater = (now.month-1)//3+1
    
    if quater == 1:
        quater = 4
    else:
        quater = quater - 1
    
    fiscal = f'{quater}Q{now.year}'
    
    if earnings_df['quarterly_results']['date'].values[-1] != fiscal:
        continue
    else:
        quarterly_results = earnings_df['quarterly_results'].loc[a['quarterly_results']['date'] == fiscal].values.tolist()
        actual = quarterly_results[0][1]
        estimate = quarterly_results[0][2]
            
    if actual < estimate:
  
        for event in events:
            #print(event['summary'])
            if event['summary'] == f'{ticker} Missed Earnings':
                print(f"{ticker} event already exists")
                break
            else:
                # Create new event
                title = f'{ticker} Missed Earnings'
                day = datetime.strptime(value, '%Y-%m-%d').date() + timedelta(days=4)
                day = day.strftime('%Y-%m-%d')
                create_event(title, value, value, calendar_id=calendar_id, colour=8)                    

                print(f'Creating missed earnings event {ticker}')

# print('')
# sys.stdout = backup
# f.close()  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    