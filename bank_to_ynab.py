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
import json
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

with open('/home/pi/bank-to-ynab/dev_bank_tokens.json') as json_file:
    data = json.load(json_file)

from plaid import Client as PlaidClient
from plaid import errors as PlaidErrors

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

def get_some_transactions(access_token: str, start_date: str, end_date: str) -> List[dict]:
    try:
        transactions_response = client.Transactions.get(access_token, start_date, end_date, count=500) # Max number of transactions is 500 default is 100
    except PlaidErrors.PlaidError as e:
        send_email("Exception when calling TransactionsApi->getTransactions: %s\n" % e, e.code)
    return transactions_response


def cleanup_transactions(transactions: list, account):
    entriesToRemove = ('category', 'category_id') # Category from Plaid API is different to those in YNAB
    for a in transactions:
        a['payee_name'] = a.pop('name')
        a['account_id'] = account # Match bank access token to ynab acount id
        a['import_id'] = a['date'] + '-' + a['transaction_id'][:25] # Pervent duplications in ynab
        a['amount'] = int(a['amount'] * -1000) # YNAB uses milliunits, 1,000 milliunits equals "one" unit
        a['cleared'] = 'cleared' # Plaid API only gets cleared transactions
        for k in entriesToRemove:
            a.pop(k, None)
    return transactions

def send_email(msg: str, error_code):
    sender_email = os.getenv('GMAIL')
    receiver_email = os.getenv('MY_EMAIL')
    #password = 'QN%z97QLf'

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

def job():
    today = date.today()
    first = today.replace(day=1)
    lastMonth = first - timedelta(days=1)
    for p in data['banks']:
        account_id = p['ynab_account_id']
        #print(p['access_token'])
        #print(lastMonth.strftime("%Y-%m-%d"))
        #print(today.strftime("%Y-%m-%d"))
        some_transactions = get_some_transactions(p['access_token'], lastMonth.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        transactions = cleanup_transactions(some_transactions['transactions'], account_id)
    
        """
        Note:
        In Plaid API, Positive values when money moves out of the account; negative values when money moves in.
        For example, purchases are positive; credit card payments, direct deposits, refunds are negative.
        """
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S") 
        pprint(f"{now}: there are {some_transactions['total_transactions']} total transations this month in {p['name']}")
        
        import ynab
        from ynab.rest import ApiException
    
        configuration = ynab.Configuration()
    
        configuration.api_key['Authorization'] = os.getenv('YNAB_API_KEY')
        configuration.api_key_prefix['Authorization'] = 'Bearer'
    
        api_instance = ynab.TransactionsApi(ynab.ApiClient(configuration))
        budget_id = os.getenv('YNAB_BUDGET_ID')
    
        bulk_transactions = ynab.BulkTransactions(transactions)
    
        try:
            # Bulk create transactions
            api_response = api_instance.bulk_create_transactions(budget_id, bulk_transactions)
            #pprint(api_response)
        except ApiException as e:
            print("Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e.reason)
            send_email("Exception when calling TransactionsApi->bulk_create_transactions: %s\n" % e.reason ,e.status)


schedule.every(30).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)


















