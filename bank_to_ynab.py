#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  4 05:11:37 2020

@author: David
"""
import os
from pprint import pprint
from typing import List
from datetime import date, timedelta, datetime
import time
import schedule
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from data import get_tokens
import ynab
from ynab.rest import ApiException
from plaid import Client as PlaidClient
from plaid import errors as PlaidErrors

data = get_tokens()

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')

WORKING_ENV = os.getenv('WORKING_ENV', 'development')

# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV = os.getenv('PLAID_ENV', 'development')
client = PlaidClient(client_id = PLAID_CLIENT_ID, secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY, environment=PLAID_ENV)

today = date.today()
first = today.replace(day=1)
lastMonth = first - timedelta(days=14) # 200 requests per hour rate limit

def get_some_transactions(access_token: str, start_date: str, end_date: str) -> List[dict]:
    try:
        transactions_response = client.Transactions.get(access_token, start_date, end_date, count=500) # Max number of transactions is 500 default is 100
    except PlaidErrors.PlaidError as e:
        
        if e.code == 'ITEM_LOGIN_REQUIRED':
             
            ## Plaid Institution name
            bb = client.Accounts.get(access_token)['item']['institution_id']
            bank = client.Institutions.get_by_id(bb)['institution']['name']
                        
            # The users' login information has changed, generate a public_token for the account
            # Create a one-time use public_token for the Item.
            # This public_token can be used to initialize Link in update mode for the user.
            public_token = client.Item.public_token.create(access_token)['public_token']
            
            send_email(f"Plaid: Update required for bank account {bank}. Public token: {public_token}\n", e.code)
            
            # initialize Link in update mode to restore access to this user's data
            # Done using flask
            # see https://plaid.com/docs/api/#updating-items-via-link
        else:
            print("Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e.reason)
            send_email("Plaid: Exception when calling TransactionsApi->getTransactions: %s\n" % e, e.code)
    return transactions_response

def cleanup_transactions(transactions: list, account):
    entriesToRemove = ('category', 'category_id') # Category from Plaid API is different to those in YNAB
    for a in transactions:
        a['payee_name'] = a.pop('name')
        a['account_id'] = account # Match bank access token to ynab acount id
        a['import_id'] = a['date'] + '-' + a['transaction_id'][:25] # Prevent duplications in ynab
        a['amount'] = int(a['amount'] * -1000) # YNAB uses milliunits, 1,000 milliunits equals "one" unit
        #a['cleared'] = 'cleared' # Plaid API only gets cleared transactions
        for k in entriesToRemove:
            a.pop(k, None)
    return transactions

def send_email(msg: str, error_code):
    sender_email = os.getenv('GMAIL')
    receiver_email = os.getenv('MY_EMAIL')

    message = MIMEMultipart("alternative")
    message["Subject"] = "YNAB Script Issue: [%s]" % error_code
    message["From"] = "Digital Dashboard <{}>".format(sender_email)
    message["To"] = os.getenv('MY_EMAIL')

    port = os.getenv('GMAIL_PORT')  # For SSL

    part1 = MIMEText(msg, "plain")
    message.attach(part1)

    # Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(os.getenv('GMAIL'), os.getenv('GMAIL_PASS'))
        # TODO: Send email here
        server.sendmail(sender_email, receiver_email, message.as_string())

def send_transactions(row):
    
    account_id = row['ynab_account_id']
    
    ## Plaid Institution name
    # bb = client.Accounts.get(row['access_token'])['item']['institution_id']
    # bank = client.Institutions.get_by_id(bb)['institution']['name']
    
    some_transactions = get_some_transactions(row['access_token'], lastMonth.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
    transactions = cleanup_transactions(some_transactions['transactions'], account_id)

    """
    Note:
    In Plaid API, Positive values when money moves out of the account; negative values when money moves in.
    For example, purchases are positive; credit card payments, direct deposits, refunds are negative.
    """
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S") 
    pprint(f"{now}: there have been {some_transactions['total_transactions']} total transations in the past 2 weeks from {row['bank']}")
     
    configuration = ynab.Configuration()

    configuration.api_key['Authorization'] = os.getenv('YNAB_API_KEY')
    configuration.api_key_prefix['Authorization'] = 'Bearer'

    api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
    budget_id = os.getenv('YNAB_BUDGET_ID')
    
    # YNAB have depricated bulk transactions endpoint 
    # as a result sending empty arrays returns an error 
    if len(transactions) > 0 : 

        bulk_transactions = ynab.BulkTransactions(transactions)

        try:
            # Bulk create transactions
            api_response = api_instance.bulk_create_transactions(budget_id, bulk_transactions) #depricated
            #pprint(api_response)
        except ApiException as e:
            print("Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e.reason)
            send_email("YNAB: Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e.reason ,e.status)
            
            if e.status == 429:
                # Too Many Requests
                exit()
    return row
    
def job():
    data.apply(send_transactions, axis=1)
    #for i, row in data.iterrows():        

if WORKING_ENV == 'development':            
    schedule.every(10).seconds.do(job)
else:
    schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)


















