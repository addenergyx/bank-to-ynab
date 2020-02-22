#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 16:33:58 2020

@author: David
"""

import os
from typing import List
import schedule

from calendar import monthrange
from datetime import datetime
import time

import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from plaid import Client as PlaidClient

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV = os.getenv('PLAID_ENV', 'development')

client = PlaidClient(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV)

email_triggered = False # Global Variable
 
def get_some_transactions(access_token: str, start_date: str, end_date: str) -> List[dict]:
    return client.Transactions.get(access_token, start_date, end_date)['transactions']

def num_of_card_transations(transactions: list):
    num = 0
    excluded_categories = ['Credit', 'Transfer']
    for a in transactions:
        if excluded_categories[0] not in a['category'] and excluded_categories[1] not in a['category']:
            num+=1
    return num

def send_email(num):
    
    global email_triggered
    if not email_triggered:
        sender_email = os.getenv('GMAIL')
        receiver_email = os.getenv('MY_EMAIL')
        #password = 'QN%z97QLf'
        
        message = MIMEMultipart("alternative")
        message["Subject"] = "Time to switch cards!!!" 
        message["From"] = "Digital Dashboard <{}>".format(sender_email)
        message["To"] = os.getenv('MY_EMAIL')
        
        text = 'You have completed {} Transactions'.format(num)
                
        port = os.getenv('GMAIL_PORT')  # For SSL
        
        email_triggered = True
        
        part1 = MIMEText(text, "plain")
        message.attach(part1)
        
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(os.getenv('GMAIL'), os.getenv('GMAIL_PASS'))
            # TODO: Send email here
            server.sendmail(sender_email, receiver_email, message.as_string())

def job():
    lastDay = monthrange(2020, 2)[1]
    currentMonth = '{:02d}'.format(datetime.now().month)
    currentYear = datetime.now().year

    if datetime.now().day == 1:
       global email_triggered
       email_triggered = False # Reset email at beginning of the month
    
    some_transactions = get_some_transactions(os.getenv('COOP_ACCESS_TOKEN'), "{0}-{1}-01".format(currentYear,currentMonth), 
                                              "{0}-{1}-{2}".format(currentYear,currentMonth,lastDay))
    
    num = num_of_card_transations(some_transactions)
    print(num)
    if num >= 30:
        send_email(num)

schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
























