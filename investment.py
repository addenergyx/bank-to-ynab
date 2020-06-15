# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:59:21 2020

@author: david
"""

import imaplib
import base64
import os
import email
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# -------------------------------------------------
#
# Utility to read Contract Note Statement from Trading212 from Gmail Using Python
# Trading 212 currently doesn't let you export files to csv format
#
# ------------------------------------------------

email_user = os.getenv('GMAIL')
email_pass = os.getenv('GMAIL_PASS')

port = 993

SMTP_SERVER = "imap.gmail.com"

mail = imaplib.IMAP4_SSL(SMTP_SERVER)

mail.login(email_user, email_pass)

mail.select('investing')

status, mailbox = mail.search(None, 'ALL')

data = []
column_headers = ['Order ID', 'Ticker Symbol', 'Type', 
                  'Shares', 'Price', 'Total amount', 'Trading day', 
                  'Trading time', 'Commission', 'Charges and fees', 'Order Type', 
                  'Execution venue', 'Exchange rate', 'Total cost']

mailbox_list = mailbox[0].split()

for item in mailbox_list:
    
# for num in data[0].split():
    status, body = mail.fetch(item, '(RFC822)')
    email_msg = body[0][1]

    raw_email = email_msg.decode('utf-8')

    email_message = email.message_from_bytes(email_msg)

    counter = 1
    for part in email_message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        filename = part.get_filename()
        if not filename:
            ext = '.html'
            filename = 'msg-part%08d%s' %(counter, ext)
        
        counter += 1
        
        content_type = part.get_content_type()
        # print(content_type)
        
        if "html" in content_type:
            html_ = part.get_payload()
            soup = BeautifulSoup(html_, 'html.parser')
        
            inv = soup.select('table[class*="report"]')
            table_list = []
            
            for table in inv:
                rows = table.findChildren('tr')
                for row in rows:
                    row_list = []
                    # cells = row.find_all(['th', 'td'], recursive=False)
                    cells = row.find_all('td', recursive=False)
                    for cell in cells:
                        value = cell.string                
                        if value:
                            row_list.append(value.strip())
                            #print(value.strip())
                    if row_list:
                        data.append(row_list[1:])
    
portfolio = pd.DataFrame(data, columns=column_headers)

# ace.columns = ace.columns.str[4:]
# ace.drop('No', axis=1, inplace=True)

# for column in portfolio.columns:
#     portfolio[column] = portfolio[column].str.rstrip('GBP') 

float_values = ['Shares', 'Price', 'Total amount','Commission', 'Charges and fees','Total cost', 'Exchange rate']

for column in float_values:
    portfolio[column] = portfolio[column].str.rstrip('GBP').astype(float)

# Remove unnecessary ISN number 
portfolio['Ticker Symbol'] = portfolio['Ticker Symbol'].str.split('/', 1).str[0]

# Airbus changed their ticker symbol
portfolio['Ticker Symbol'].replace('AIRp', 'AIR', inplace=True)

portfolio['Trading day'] = pd.to_datetime(portfolio['Trading day'], format='%d-%m-%Y') #pd.to_datetime(portfolio["Trading day"]).dt.strftime('%m-%d-%Y')

## For getting ROI Dataframe needs to be ordered in ascending order and grouped by Ticker Symbol
portfolio.sort_values(['Ticker Symbol','Trading day','Trading time'], inplace=True, ascending=True)

# # Datetime not compatible with excel
portfolio['Trading day'] = portfolio['Trading day'].dt.strftime('%d-%m-%Y')


'''
Things to take note when creating a Transactions Portfolio for Simply Wall St:

For stocks that have a currency other than your portfolio’s base currency, the entry should be based on the original listing currency. 
The system will automatically convert it to the currency you have chosen for your portfolio. 
If you enter a converted price, it will create a wrong converted value, as if the value will be converted twice. 

https://support.simplywall.st/hc/en-us/articles/360001480916-How-to-Create-a-Portfolio

'''

simply_wall_st = portfolio.filter(['Ticker Symbol', 'Trading day', 'Shares', 'Price', 'Total amount', 'Type', 'Exchange rate'], axis=1)

#simply_wall_st['Total amount'] = simply_wall_st['Total amount'].astype(float)
# simply_wall_st['Exchange rate'] = simply_wall_st['Exchange rate'].astype(float)
# simply_wall_st['Price'] = simply_wall_st['Price'].astype(float)

simply_wall_st['Exchange rate'] = simply_wall_st['Exchange rate'].replace(0.01, 1)

simply_wall_st['Price'] = simply_wall_st['Price'] / simply_wall_st['Exchange rate']

simply_wall_st.to_csv('Simply Wall St Portfolio.csv', index=False)
portfolio.to_csv('Investment Portfolio.csv', index=False )

# import pandas as pd
# df = pd.read_csv('test.csv')
# #df.drop(df.tail(1).index,inplace=True)

# num_of_sells = len(df[df.Type == 'Sell'])

# weighted_average = 0
# num_of_stocks = 0
# rotation = 1

# a = df[df.Type == 'Sell']

# for i_, sell_row in a.iterrows():
    
#     cumulative_total = 0
#     cumulative_stock = 0
    
#     stok_lis =[]
#     price_lis =[]
    
#     for i, row in df.iterrows():
        
#         if row['Type'] == 'Buy':
#             print('Buy Order')
            
#             stok_lis.append(row['Shares'])
#             price_lis.append(row['Price'])
            
            
#             ## This order's price_per_share
#             # current_average = ( row['Shares'] * row['Price'] ) / row['Shares']
            
#             ## if first price per average
#             # if cumulative_average == 0:
#             #     cumulative_stock = row['Shares']
#             #     cumulative_total = row['Total cost']
#             # else:
#             #     cumulative_stock += row['Shares']
#             #     cumulative_average = (cumulative_average + current_average) / cumulative_stock
                        
#         elif i_ == i:
            
#             cumulative_average = (df['Shares'][:i_] * df['Price'][:i_]).sum() / df['Shares'][:i_].sum() #works for first sale
            
#             #print(row)
#             print(f'Average: {cumulative_average}')
#             profit_per_share = row['Price'] - cumulative_average
#             gain_loss = profit_per_share * sell_row['Shares']
#             print('Sell Off')
#             print(f'Gain/Loss: {gain_loss}')
#             print('-----------------')
#             break
        
#         ## if a sell type row['Type'] == 'Sell':
#         else :
#             print('remove share from weighted')

all_holdings = portfolio['Ticker Symbol'].unique()

import pandas as pd

# returns_dict = {}
total_returns = 0

import collections
holdings_dict = collections.defaultdict(dict)

for symbol in all_holdings:
    
    df = portfolio[portfolio['Ticker Symbol'] == symbol]
    
    df = df.reset_index().drop('index', axis=1)
        
    a = df[df.Type == 'Sell']
    
    print(f'-------{symbol}-------')
    
    for ii, sell_row in a.iterrows():
        
        ## currently does not take into account fees 
        ## should use total cost column instead later
        
        share_lis = df['Shares'][:ii+1].tolist()
        price_lis = df['Price'][:ii+1].tolist()
        type_lis = df['Type'][:ii+1].tolist()
        
        fees_lis = df['Charges and fees'][:ii+1].tolist()
    
        c = x = holdings = average = 0
                
        for s, p, t, in list(zip(share_lis, price_lis, type_lis)):
            
            if t == 'Buy':
                c += s*p
                holdings += s
                average = c / holdings
                print(f'Buy Order: {s} @ {p}')
                print(f'Buy Order New Average: {holdings} @ {average}')
            
            else:
                ## Selling stock
                
                ## if ii == len(share_lis): <- Doesn't work, This is probably because in the Python 3.x, 
                ## zip returns a generator object. This object is not a list
                ## https://stackoverflow.com/questions/31011631/python-2-3-object-of-type-zip-has-no-len/38045805
    
                if ii == x:
                    
                    average = c / holdings
                    gain_loss = p - average
                    total_profit = gain_loss * s
                    print(f'Current Holdings Average: {holdings} @ {average}')
                    print(f'Final Sell Order: {s} @ {p}')
                    print(f'Total Return on Invesatment: {round(total_profit, 2)}')
                    total_returns += round(total_profit, 2)
                    
                    if symbol in returns_dict:
                        # returns_dict[symbol] += total_profit
                        holdings_dict[symbol]['Gross Returns'] += total_profit
                    else:
                        # returns_dict[symbol] = total_profit
                        holdings_dict[symbol]['Gross Returns'] = total_profit
                                        
                    print('-----------------')         
                    break #Use break because don't care about orders after sell order
                
                else:
                    holdings -= s 
                    print(f'Sell Order: {s} @ {p}')
                    
                    if holdings == 0:
                        ## Reset average after liquidating stock
                        average = 0
                        c = 0
                        print('Sold all holdings')
                    else:
                        print(f'New Holdings Average: {holdings} @ {average}')
                        ## Take away shares from from holding average
                        ## However average stays the same
                        c -= s*average
            x += 1

print(f'Gross Returns: {total_returns}')
net_returns = total_returns - portfolio['Charges and fees'].sum()
print(f'Net Returns: {net_returns}')

## Current holdings in portfolio

for symbol in all_holdings:
    
    df = portfolio[portfolio['Ticker Symbol'] == symbol]
    
    df = df.reset_index().drop('index', axis=1)

    print(f'-------{symbol}-------')
    
    for ii, row in df.iterrows():
        
        ## currently does not take into account fees 
        ## should use total cost column instead later
        
        share_lis = df['Shares'][:ii+1].tolist()
        price_lis = df['Price'][:ii+1].tolist()
        type_lis = df['Type'][:ii+1].tolist()
    
        c = x = holdings = average = 0
                
        for s, p, t, in list(zip(share_lis, price_lis, type_lis)):
            
            if t == 'Buy':
                c += s*p
                holdings += s
                average = c / holdings
                print(f'Buy Order: {s} @ {p}')
                print(f'Buy Order New Average: {holdings} @ {average}')
            
            else:

                holdings -= s 
                print(f'Sell Order: {s} @ {p}')
                
                if holdings == 0:
                    ## Reset average after liquidating stock
                    average = 0
                    c = 0
                    print('Sold all holdings')
                else:
                    print(f'New Holdings Average: {holdings} @ {average}')
                    ## Take away shares from from holding average
                    ## However average stays the same
                    c -= s*average
      
    holdings_dict[symbol]['Current Holdings'] = holdings
    holdings_dict[symbol]['Current Average'] = average
        
    print(f'Holdings Average: {holdings} @ {average}')            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            