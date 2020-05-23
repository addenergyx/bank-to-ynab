# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 20:34:14 2020

@author: david
"""

import os
import datetime
import plaid
import json
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

# Initialises flask application
server = Flask(__name__)

PLAID_CLIENT_ID = os.getenv('PLAID_CLIENT_ID')
PLAID_SECRET = os.getenv('PLAID_SECRET')
PLAID_PUBLIC_KEY = os.getenv('PLAID_PUBLIC_KEY')
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use development to test with live users and credentials and production
# to go live
PLAID_ENV = os.getenv('PLAID_ENV', 'development')


client = plaid.Client(
    client_id=PLAID_CLIENT_ID,
    secret=PLAID_SECRET,
    public_key=PLAID_PUBLIC_KEY,
    environment=PLAID_ENV,
)

# PLAID_PRODUCTS is a comma-separated list of products to use when initializing
# Link. Note that this list must contain 'assets' in order for the app to be
# able to create and retrieve asset reports.
PLAID_PRODUCTS = os.getenv('PLAID_PRODUCTS', 'transactions')

# PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
# will be able to select institutions from.
PLAID_COUNTRY_CODES = os.getenv('PLAID_COUNTRY_CODES', 'GB')

# Parameters used for the OAuth redirect Link flow.
#
# Set PLAID_OAUTH_REDIRECT_URI to 'http://localhost:5000/oauth-response.html'
# The OAuth redirect flow requires an endpoint on the developer's website
# that the bank website should redirect to. You will need to whitelist
# this redirect URI for your client ID through the Plaid developer dashboard
# at https://dashboard.plaid.com/team/api.
PLAID_OAUTH_REDIRECT_URI = os.getenv('PLAID_OAUTH_REDIRECT_URI', '');
# Set PLAID_OAUTH_NONCE to a unique identifier such as a UUID for each Link
# session. The nonce will be used to re-open Link upon completion of the OAuth
# redirect. The nonce must be at least 16 characters long.
PLAID_OAUTH_NONCE = os.getenv('PLAID_OAUTH_NONCE', '');

# The users' login information has changed, generate a public_token for the account
# Create a one-time use public_token for the Item.
# This public_token can be used to initialize Link in update mode for the user.
# Enter access token

access_token = 'access-development-126b5513-46c6-45c1-8117-c8b5ed9d6c61'
public_token = client.Item.public_token.create(access_token)['public_token']

# print(public_token)

@server.route('/')
def index():
  return render_template(
    'index.ejs',
    plaid_public_key=PLAID_PUBLIC_KEY,
    plaid_environment=PLAID_ENV,
    plaid_products=PLAID_PRODUCTS,
    plaid_country_codes=PLAID_COUNTRY_CODES,
    plaid_oauth_redirect_uri=PLAID_OAUTH_REDIRECT_URI,
    plaid_oauth_nonce=PLAID_OAUTH_NONCE,
  )

# This is an endpoint defined for the OAuth flow to redirect to.
@server.route('/oauth-response.html')
def oauth_response():
  return render_template(
    'oauth-response.ejs',
    plaid_public_key=PLAID_PUBLIC_KEY,
    plaid_environment=PLAID_ENV,
    plaid_products=PLAID_PRODUCTS,
    plaid_country_codes=PLAID_COUNTRY_CODES,
    plaid_oauth_nonce=PLAID_OAUTH_NONCE,
  )

@server.route('/update')
def update_creds():
    return render_template('update.ejs', plaid_public_key=PLAID_PUBLIC_KEY, plaid_environment=PLAID_ENV, public_token=public_token)

def pretty_print_response(response):
  print(json.dumps(response, indent=2, sort_keys=True))

if __name__ == '__main__':
    server.run(port=os.getenv('PORT', 5000), use_reloader=False)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    