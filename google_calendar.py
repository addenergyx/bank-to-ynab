# -*- coding: utf-8 -*-
"""
Created on Sun Jun 26 16:31:05 2022

@author: david
"""

import time
from dotenv import load_dotenv
from infrastructure.google_apis import create_service
from datetime import datetime, timedelta
import os
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.auth

load_dotenv(verbose=True, override=True)

logger = logging.getLogger()
logging.basicConfig(
    format='%(asctime)s %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S')

CALENDAR_ID = os.getenv('CALENDAR_ID')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/calendar.events']

API_NAME = 'calendar'
API_VERSION = 'v3'
CALENDAR_ID = os.getenv('CALENDAR_ID')
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')

creds = google.auth.load_credentials_from_file(SERVICE_ACCOUNT_FILE, SCOPES)[0]
service = build(API_NAME, API_VERSION, credentials=creds)

# now = (datetime.now() - timedelta(16)).strftime('%Y-%m-%dT%H:%M:%S-00:00') 
# List all events in fitness calendar
# events = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
#                                  orderBy='startTime', singleEvents=True).execute()

def get_events(time_min=datetime.now().strftime('%Y-%m-%dT%H:%M:%S-00:00'), calendar_id=CALENDAR_ID):
    return service.events().list(
        calendarId=calendar_id,
        singleEvents=True,
        orderBy='startTime',
        timeMin=time_min,
    ).execute().get('items')


def create_body(name, start, end, colour=0):
    return {
        'summary': f'{name}',
        'description': f'Don\'t forget weigh in due between {start} and {end}',
        'start': {
            'date': start,
            'timeZone': 'Europe/London',
        },
        'end': {
            'date': end,
            'timeZone': 'Europe/London',
        },
        'colorId': colour,  # 0 if weight else 11 https://lukeboyle.com/blog/posts/google-calendar-api-color-id
        # 'reminders': {
        #   'useDefault': True,
        # 'useDefault': False,
        # 'overrides': [
        #   {'method': 'email', 'minutes': 24 * 60},
        #   {'method': 'popup', 'minutes': 24 * 60},
        #   {'method': 'email', 'minutes': 48 * 60},
        #   {'method': 'popup', 'minutes': 48 * 60},
        #   #{'method': 'email', 'minutes': 168 * 60},
        #   {'method': 'popup', 'minutes': 168 * 60},
        # ],
        # # },
    }


def convert_date_for_cal(day, add_days=0):
    day = datetime.strptime(day.replace(",", ""), '%b %d %Y').date() + timedelta(days=add_days)
    return day.strftime('%Y-%m-%d')


def active(date, start: bool):

    # Change to if between dates then active elif before start else after end
    if start:
        return datetime.now() <= datetime.strptime(date.replace(",", ""), '%b %d %Y')
    else:
        return datetime.now() <= datetime.strptime(date.replace(",", ""), '%b %d %Y').replace(hour=23, minute=59, second=59, microsecond=999999)


def update_event(title, start, end, event_id, calendar_id=CALENDAR_ID, colour=0):
    logger.info(f'Updated event {title} in calendar')
    return service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=create_body(title, start, end, colour)
        ).execute()
            
def delete_event(event_Id, calendar_id=CALENDAR_ID):
    logger.info(f'Deleted event {event_Id} in calendar')
    return service.events().delete( # Deleting to keep calendar clean
        calendarId=calendar_id,
        eventId=event_Id,
        ).execute()

def create_event(title, start, end, calendar_id=CALENDAR_ID, colour=0):
    logger.info(f'Created event {title} in calendar')
    return service.events().insert(
        calendarId=calendar_id,  # Fitness
        body=create_body(title, start, end, colour)
        ).execute()
    
        
        
        
        
        
        
        
