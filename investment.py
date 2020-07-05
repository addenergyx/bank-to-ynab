# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:59:21 2020

@author: david
"""

import imaplib
import os
import email
from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dotenv import load_dotenv
import stockstats
import collections
from pandas_datareader import data as web
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prettytable import PrettyTable

load_dotenv(verbose=True, override=True)

# -------------------------------------------------
#
# Utility to read Contract Note Statement from Trading212 from Gmail Using Python
# Trading 212 currently doesn't let you export files to csv format
#
# -------------------------------------------------

## TODO: Stock allocation

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

# ------------------------------------------------           
#
# Calculates total portfolio returns and individual stock return
# Trading212 currently doesn't show total returns of individual stocks
#
# ------------------------------------------------

all_holdings = portfolio['Ticker Symbol'].unique()
watchlist = ['NIO','SMAR','RDW','PYPL','NFLX', 'RVLV', 'SMWH', 'AMZN', 'GOOGL', 'MCD', 'MSFT', 'AAPL', 'FB', 
             'WMT', 'KIE', 'WPC', 'SHOP', 'UBER', 'MTCH', 'JD.', 'DLR', 'CARD', 'FSLY', 'WKHS', 'RMV', 'TW.', 'PSN']

def returnNotMatches(a, b):
    return [x for x in b if x not in a]

## Remove stocks already in my portfolio
watchlist = returnNotMatches(all_holdings, watchlist)

total_returns = 0

holdings_dict = collections.defaultdict(dict) # Allows for nesting easily

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
                print(f'New Holdings Average: {holdings} @ {average}')
            
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
                    
                    if symbol in holdings_dict:
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

def generate_holdings(all_holdings):
    
    for symbol in all_holdings:
        
        df = portfolio[portfolio['Ticker Symbol'] == symbol]
        
        df = df.reset_index().drop('index', axis=1)
    
        ## Watchlist
        
        if df.empty:
            holdings_dict[symbol]['Current Holdings'] = 0
            holdings_dict[symbol]['Current Average'] = 0.0
        
        else:
            print(f'------- {symbol} History -------')
            
            for ii, row in df.iterrows():
                
                ## currently does not take into account fees 
                ## should use total cost column instead later
                ## trading212 doesn't include fees in returns per stock
                
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
                        print(f'New Holdings Average: {holdings} @ {average}')
                    
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
              
            holdings_dict[symbol]['Current Holdings'] = formatting(holdings)
            holdings_dict[symbol]['Current Average'] = formatting(average)
                
            print(f'Holdings Average: {holdings} @ {average}')            

# ------------------------------------------------           
#
# Relative Strength Index Indicator
#
# Also email notifications of oversold/overbought stock to review
# A stock that is oversold doesn't necessarily mean it's a good time to buy but just that
# it's a good deal relative to the rest of the price action
#
# ------------------------------------------------

"""
              100
RSI = 100 - --------
             1 + RS

RS = Average Gain / Average Loss

The very first calculations for average gain and average loss are simple
14-period averages:

First Average Gain = Sum of Gains over the past 14 periods / 14.
First Average Loss = Sum of Losses over the past 14 periods / 14

The second, and subsequent, calculations are based on the prior averages
and the current gain loss:

"""
#rsi_dict = {}

# Trading 212 stock list [Invest] google sheet (separators ";", encoding = "utf_16")
stock_list_lookup = pd.read_csv('trading212-INVEST.csv' , encoding = "utf_16", sep=';')

#AIR.PA ABF.L 
# use lookup table 

# symbol = 'ABF'

# looky = stock_list_lookup.loc[stock_list_lookup['ticker'] == symbol]

# market_name = a.head(1).to_string(index=False).strip()

# if looky['Market name '].head(1).to_string(index=False).strip() is 'London Stock Exchange':
#     symbol = f'{symbol}.L'
# elif looky['Market name '].head(1).to_string(index=False).strip() is 'London Stock Exchange':   
    
start = datetime.datetime(2020, 2, 8)
end = datetime.datetime.now()    

def formatting(num):
    return round(num, 2)

def generate_rsi(all_holdings):
    
    for symbol in all_holdings:
    
        try:
            
            looky = stock_list_lookup.loc[stock_list_lookup['ticker'] == symbol]
            if looky['Market name '].head(1).to_string(index=False).strip() == 'London Stock Exchange':
                #remove trailing . from BA. (BAE SYSTEMS)
                yf_symbol = symbol.rstrip('.')
                yf_symbol = f'{yf_symbol}.L'
            elif symbol == 'KWS' or symbol == 'RDSB':
                yf_symbol = f'{symbol}.L'            
            elif symbol == 'EXSH':
                yf_symbol = f'{symbol}.MI'
            else:
                yf_symbol = symbol
            
            index = web.DataReader(yf_symbol, 'yahoo', start, end)
            
            holdings_dict[symbol]['Today Open'] = formatting(index['Open'][-1])
            holdings_dict[symbol]['1D'] = formatting(index['Close'][-2])
            holdings_dict[symbol]['1W'] = formatting(index['Close'][-6])
            holdings_dict[symbol]['1M'] = formatting(index['Close'][-29])
            
            ## Rearrange dataframe for stockstats module
            cols = ['Open','Close','High','Low', 'Volume','Adj Close']
        
            index = index[cols]
            
            ## https://github.com/jealous/stockstats
            stock = stockstats.StockDataFrame.retype(index)
            
            print('{}: {}'.format(symbol, stock.get('rsi_13')[-1]))
            
            gg = formatting(stock.get('close_9_sma')[-2]) # Price strength SMA line
            qq = formatting(stock.get('close_180_sma')[-2]) # Directional SMA line
            
            if stock['open'][-2] > stock['close'][-2]:
                # Trending downward
                if stock['close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed downward' #potential sell
                elif gg > stock['close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock'
                    
                    
                if qq > stock['close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock'
                
            else:
                #Trending upward
                if stock['close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed upward' #potential buy
                elif gg > stock['close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock'
            
                if qq > stock['close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock'
            
            
            holdings_dict[symbol]['RSI'] = formatting(stock.get('rsi_13')[-1])
        except:
            print(f"Couldn't find symbol {symbol} in lookup table")
            pass
    
def send_email(rsi_dict):
    
    sender_email = os.getenv('GMAIL')
    receiver_email = os.getenv('MY_EMAIL')
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Daily RSI Alert" 
    message["From"] = "Daily RSI Alert - Digital Dashboard <{}>".format(sender_email)
    message["To"] = os.getenv('MY_EMAIL')
    
    #text = 'You have completed {} Transactions'.format(num)

    x = PrettyTable(['Ticker','Current Holdings','Current Average', '1M', '1W', '1D','Today Open', '9_SMA', '180_SMA', 'RSI'])
    x.align = "c" 
    
    for key, val in holdings_dict.items():
       x.add_row([key, val['Current Holdings'], val['Current Average'], val['1M'], val['1W'], val['1D'], val['Today Open'], val['9_sma'], val['180_sma'], val['RSI']])
    
    x.sortby = "RSI"
    
    html = x.get_html_string(attributes={"name":"stocks_table"})
    
    # plain = x.get_string()
    
    # print(x)
    # print (html)

    port = os.getenv('GMAIL_PORT')  # For SSL
        
    part1 = MIMEText(html, "html")
    message.attach(part1)
    
    # Create a secure SSL context
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(os.getenv('GMAIL'), os.getenv('GMAIL_PASS'))
        # TODO: Send email here
        server.sendmail(sender_email, receiver_email, message.as_string())

## Current holdings in portfolio
generate_holdings(all_holdings)

## Add watchlist for html table
generate_holdings(watchlist)

generate_rsi(all_holdings)
generate_rsi(watchlist)

send_email(holdings_dict)









            
            
            
            
            
            
            
            
            