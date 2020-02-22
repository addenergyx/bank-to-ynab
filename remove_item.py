#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 13:09:06 2020

@author: ubu
"""

import os
import json

with open('/home/ubu/Desktop/bank_tokens.json') as json_file:
    data = json.load(json_file)

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

access_token = 'access-development-3f84aab6-dd1c-4303-8d5c-55ba5273d962'
client.Item.remove(access_token)