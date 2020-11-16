# -*- coding: utf-8 -*-
"""
Created on Sat May  2 08:59:21 2020

@author: david
"""

import imaplib
import os
import email
from bs4 import BeautifulSoup
import requests 
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
import re

load_dotenv(verbose=True, override=True)

# -------------------------------------------------
#
# Utility to read Contract Note Statement from Trading212 from Gmail using Python
# Trading 212 currently doesn't have an API or let you export files to csv format
#
# -------------------------------------------------

##### TODO #####
# Stock allocation %
# Graphs with points of buy/sell days (similar to vanguard)
# withdraws/deposits (email: Withdrawal request successful/Real Account Funded Successfully)
# Monthly dividends (from Monthly statement email)
# UK vs US portfolio (compare returns in all markets)
# Move equities table to a database and keep old tickers (update table instead of creating new one each time)
# Fix watchlist

email_user = os.getenv('GMAIL')
email_pass = os.getenv('GMAIL_PASS') # Make sure 'Less secure app access' is turned on

port = 993

SMTP_SERVER = "imap.gmail.com"

## Creating portfolio

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

## Scraping Trading212 site ##

## Stocks
## Need this to put the right trailing value for yahoo finance (i.e .L/.MI)
url = "https://www.trading212.com/en/Trade-Equities"

headers = {
    'User-Agent': 'My User Agent 1.0',
}

r = requests.get(url, headers=headers)

#print(r.content) 

soup = BeautifulSoup(r.content, 'html5lib')

table = soup.find('div', attrs = {'id':'all-equities'})

instruments = []
for row in table.findAll('div', id=lambda x: x and x.startswith('equity-row-')):
    instrument = {}
    instrument['INSTRUMENT'] = row.find('div', attrs = {'data-label':'Instrument'}).text
    instrument['COMPANY'] = row.find('div', attrs = {'data-label':'Company'}).text
    # instrument['CURRENCY CODE'] = row.find('div', attrs = {'data-label':'Currency code'}).text
    instrument['ISIN'] = row.find('div', attrs = {'data-label':'ISIN'}).text
    # instrument['MIN TRADED QUANTITY'] = row.find('div', attrs = {'data-label':'Min traded quantity'}).text
    instrument['MARKET NAME'] = row.find('div', attrs = {'data-label':'Market name'}).text
    # instrument['MARKET HOURS (GMT)'] = row.find('div', attrs = {'data-label':'Market hours (GMT)'}).text
    instruments.append(instrument)
 
all_212_equities = pd.DataFrame(instruments)

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

## Monthly summary

mail.select('dividends')

status, mailbox = mail.search(None, 'ALL')

mailbox_list = mailbox[0].split()

data = []

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
        
        summary = ['Date', 'Dividends', 'Opening balance', 'Closing balance']
        
        if "html" in content_type:
            html_ = part.get_payload()
            soup = BeautifulSoup(html_, 'html.parser')
        
            # Doesn't work, half info box missing
            # inv = soup.select('table[class*="info"]')[1] # Use inspect tool in outlook not gmail because classnames don't appear in gmail
            # rows = inv.findChildren(['th', 'tr'])
            
            row_list = []
            
            month = soup.find(text=re.compile('Closed transactions'))
            month = re.sub('[^0-9-]','', month)
            
            row_list.append(month)
            
            for x in summary[1:]:
                value = float(re.sub('[^0-9.]', '', soup.find(text=re.compile(x)).findNext('td').text))
                row_list.append(value)
            
            data.append(row_list)

summary_df = pd.DataFrame(data, columns=summary)

now = datetime.datetime.now()

summary_df.loc[len(summary_df)] = [f'{now.year}-{now.month}' , '-', summary_df.loc[len(summary_df)-1]['Closing balance'], '-']
 
summary_df['Target'] = summary_df['Opening balance'] * .05 # Aim for 5% returns a month

# ace.columns = ace.columns.str[4:]
# ace.drop('No', axis=1, inplace=True)

# for column in portfolio.columns:
#     portfolio[column] = portfolio[column].str.rstrip('GBP') 

float_values = ['Shares', 'Price', 'Total amount','Commission', 'Charges and fees','Total cost', 'Exchange rate']

for column in float_values:
    portfolio[column] = portfolio[column].str.rstrip('GBP').astype(float)

## Split ISIN and stock, need ISIN because some companies have the same ticker symbol, ISIN is the uid
portfolio[['Ticker Symbol', 'ISIN']] = portfolio['Ticker Symbol'].str.split('/', expand=True)

## TODO: Temp fix by changing DTG to Jet2, Dartgroup changed their ticker symbol to JET2
portfolio.replace('DTG','JET2', inplace=True)

## Airbus changed their ticker symbol
portfolio['Ticker Symbol'].replace('AIRp', 'AIR', inplace=True)

portfolio['Trading day'] = pd.to_datetime(portfolio['Trading day'], format='%d-%m-%Y', dayfirst=True) #pd.to_datetime(portfolio["Trading day"]).dt.strftime('%m-%d-%Y')

## For getting ROI, Dataframe needs to be ordered in ascending order and grouped by Ticker Symbol
portfolio.sort_values(['Ticker Symbol','Trading day','Trading time'], inplace=True, ascending=True)

## Datetime not compatible with excel
#portfolio['Trading day'] = pd.to_datetime(portfolio['Trading day'], dayfirst=True)

## Look into combining tickers using code like this 
## gb.loc[gb["geo_code"]=="E41000052",'geo_code'] = "E06000052" (Visual Analytics Week 7 lab007)

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

# all_holdings = portfolio['Ticker Symbol'].unique()

## Getting all tickers and isin from portfolio
temp_df = portfolio.drop_duplicates('Ticker Symbol')

all_holdings = temp_df[['Ticker Symbol', 'ISIN']] 

watchlist = ['NIO','SMAR','RDW','PYPL','NFLX', 'RVLV', 'SMWH', 'AMZN', 'GOOGL', 'MCD', 'MSFT', 'AAPL', 'FB', 
             'WMT', 'KIE', 'WPC', 'SHOP', 'UBER', 'MTCH', 'JD.', 'DLR', 'CARD', 'FSLY', 'WKHS', 'RMV', 'TW.', 'PSN', 'MU', 'AMD']

def returnNotMatches(a, b):
    return [x for x in b if x not in a]

## Remove stocks already in my portfolio
watchlist = returnNotMatches(all_holdings['Ticker Symbol'].tolist(), watchlist)

total_returns = 0

holdings_dict = collections.defaultdict(dict) # Allows for nesting easily
returns_dict = {}

for symbol in all_holdings['Ticker Symbol'].tolist():
    
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
        day_lis = df['Trading day'][:ii+1].tolist()
        
        #fees_lis = df['Charges and fees'][:ii+1].tolist()
    
        c = x = holdings = average = 0
                
        for s, p, t, d in list(zip(share_lis, price_lis, type_lis, day_lis)):
            
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
                                              
                    if d in returns_dict:    
                        returns_dict[d] += total_profit
                    else:
                        returns_dict[d] = total_profit
                                            
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

## Returns period

daily_returns_df = pd.DataFrame(returns_dict.items(), columns=['Date', 'Returns'])
daily_returns_df['Date']= pd.to_datetime(daily_returns_df['Date'], format='%d-%m-%Y') 

# Fill missing days
idx = pd.bdate_range(min(daily_returns_df.Date), max(daily_returns_df.Date))
daily_returns_df.set_index('Date', inplace=True)
#s.index = pd.DatetimeIndex(s.index)
daily_returns_df = daily_returns_df.reindex(idx, fill_value=0).reset_index().rename(columns={'index':'Date'})

# Monthly Returns
period = daily_returns_df.Date.dt.to_period("M")
g = daily_returns_df.groupby(period)
monthly_returns_df = g.sum()

# Weekly Returns
period = daily_returns_df.Date.dt.to_period("W")
g = daily_returns_df.groupby(period)
weekly_returns_df = g.sum()

##

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
            
                c = holdings = average = 0 
                #= x
                        
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
#stock_list_lookup = pd.read_csv('trading212-INVEST.csv' , encoding = "utf_16", sep=';')

#AIR.PA ABF.L 
# use lookup table 

# symbol = 'ABF'

# looky = stock_list_lookup.loc[stock_list_lookup['ticker'] == symbol]

# market_name = a.head(1).to_string(index=False).strip()

# if looky['Market name '].head(1).to_string(index=False).strip() is 'London Stock Exchange':
#     symbol = f'{symbol}.L'
# elif looky['Market name '].head(1).to_string(index=False).strip() is 'London Stock Exchange':   
    
start = datetime.datetime(2020, 2, 8) # 3 Months before I started trading 
end = datetime.datetime.now()    

def formatting(num):
    return round(num, 2)

#all_212_equities['MARKET NAME'].unique()

## For the yahoo finance api, stocks outside of the US have trailing symbols to state which market they are from

def get_yf_symbol(market, symbol):
    if market == 'London Stock Exchange' or market == 'LSE AIM':
        symbol = symbol.rstrip('.')
        yf_symbol = f'{symbol}.L'
    elif market == 'Deutsche Börse Xetra':
        yf_symbol = f'{symbol}.DE'
    elif market == 'Bolsa de Madrid':
        yf_symbol = f'{symbol}.MC'
    elif market == 'Euronext Netherlands':
        yf_symbol = f'{symbol}.AS'
    elif market == 'SIX Swiss':
        yf_symbol = f'{symbol}.SW'
    elif market == 'Euronext Paris':
        yf_symbol = f'{symbol}.PA'
    else:
        yf_symbol = symbol
    return yf_symbol


def generate_rsi(all_holdings):
    
    # stoky = set(['KWS', 'RDSB', 'FEVR'])
    
    for row in all_holdings.iloc:
    
        symbol = row[0]
        isin = row[1] ## Used in dataframe query, do not delete
        old_symbol = ''
        
        try:
            
            # print(symbol)
            # print(isin)
            
            ## When tickers change (due to mergers or company moving market) 212 removes the old ticker from the equities table
            ## As 212 doesn't provide the company name in the daily statement there is no way for me to link old tickers with the new one
            ## so will manually replace tickers here
            
            if symbol == 'AO.':
                old_symbol = symbol
                symbol = symbol.rstrip('.')
            elif symbol == 'DTG':
                old_symbol = symbol
                symbol = 'JET2'
            elif symbol == 'FMCI':
                old_symbol = symbol
                symbol = 'TTCF'
            elif symbol == 'SHLL':
                old_symbol = symbol
                symbol = 'HYLN'
            
            markets = all_212_equities.query('ISIN==@isin and INSTRUMENT==@symbol')['MARKET NAME']
            
            if len(markets) == 0:
                market = all_212_equities[all_212_equities['INSTRUMENT'] == symbol]['MARKET NAME'].item() 
            else:
                market = markets.values[0]

            #if len(market) == 0: print(len(market)) 
                
            yf_symbol = get_yf_symbol(market, symbol)    
                     
            index = web.DataReader(yf_symbol, 'yahoo', start, end)

            ## As Keys cannot be changed symbol will go back to old symbol
            ## TODO: look into adding a new key with new symbol and all values then remove the old one
            
            if old_symbol: 
                if len(index) <= 180: # Due to 180 sma dataframe needs to be atleast 180
                    ## Joining data from old and new ticker
                    index2 = web.DataReader(old_symbol, 'yahoo', start, end)
                    last_record = index2.index[-1] #Last index of old dataframe
                    index = index[index.index > last_record]
                    index = index2.append(index)
                
                symbol = old_symbol # Change symbol back to old ticker
            
            # Using adjusted closing price as it amends a stock's closing price to reflect that stock's value after 
            # accounting for any corporate actions such as Stock Splits, Dividends and Rights Offerings
            holdings_dict[symbol]['Today Open'] = formatting(index['Open'][-1])
            holdings_dict[symbol]['1D'] = formatting(index['Adj Close'][-2])
            holdings_dict[symbol]['1W'] = formatting(index['Adj Close'][-6])
            holdings_dict[symbol]['1M'] = formatting(index['Adj Close'][-29])
            
            ## Rearrange dataframe for stockstats module
            cols = ['Open','Close','High','Low', 'Volume','Adj Close']
        
            index = index[cols]
            
            ## https://github.com/jealous/stockstats
            stock = stockstats.StockDataFrame.retype(index)
            
            print('{}: {}'.format(symbol, stock.get('rsi_13')[-1]))
            
            gg = formatting(stock.get('close_9_sma')[-2]) # Price strength SMA line
            qq = formatting(stock.get('close_180_sma')[-2]) # Directional SMA line
            
            # if stock['open'][-2] > stock['close'][-2]:
            if stock['adj close'][-3] > stock['adj close'][-2]:
                # Trending downward
                if stock['adj close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed downward ↓' #potential sell
                elif gg > stock['adj close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock ↓'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock ↓'
                    
                    
                if qq > stock['adj close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock ↓'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock ↓'
                
            else:
                #Trending upward
                if stock['adj close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed upward ↓' #potential buy
                elif gg > stock['adj close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock ↑'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock ↑'
            
                if qq > stock['adj close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock ↑'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock ↑'
            
            
            holdings_dict[symbol]['RSI'] = formatting(stock.get('rsi_13')[-1])
        except IndexError as e:
            print(f"Not enough data on Stock {symbol} for RSI")
            print(e)
            pass
        except Exception as e:
            print(f"Couldn't find symbol {symbol} in lookup table")
            print(e)
            pass

def generate_rsi_watchlist(all_holdings):
    
    #stoky = set(['KWS', 'RDSB', 'FEVR'])
    
    for symbol in watchlist:
    
        try:
              
            market = all_212_equities[all_212_equities['INSTRUMENT'] == symbol]['MARKET NAME'].values[0] 
            
            yf_symbol = get_yf_symbol(market, symbol)    
            
            index = web.DataReader(yf_symbol, 'yahoo', start, end)
            
            holdings_dict[symbol]['Today Open'] = formatting(index['Open'][-1])
            holdings_dict[symbol]['1D'] = formatting(index['Adj Close'][-2])
            holdings_dict[symbol]['1W'] = formatting(index['Adj Close'][-6])
            holdings_dict[symbol]['1M'] = formatting(index['Adj Close'][-29])
            
            ## Rearrange dataframe for stockstats module
            cols = ['Open','Close','High','Low', 'Volume','Adj Close']
        
            index = index[cols]
            
            ## https://github.com/jealous/stockstats
            stock = stockstats.StockDataFrame.retype(index)
            
            print('{}: {}'.format(symbol, stock.get('rsi_13')[-1]))
            
            gg = formatting(stock.get('close_9_sma')[-2]) # Price strength SMA line
            qq = formatting(stock.get('close_180_sma')[-2]) # Directional SMA line
            
            # if stock['open'][-2] > stock['close'][-2]:
            if stock['adj close'][-3] > stock['adj close'][-2]:
                # Trending downward
                if stock['adj close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed downward ↓' #potential sell
                elif gg > stock['adj close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock ↓'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock ↓'
                    
                    
                if qq > stock['adj close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock ↓'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock ↓'
                
            else:
                #Trending upward
                if stock['adj close'][-2] <= gg <= stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Crossed upward ↓' #potential buy
                elif gg > stock['adj close'][-2] and gg > stock['open'][-2]:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Above stock ↑'
                else:
                    holdings_dict[symbol]['9_sma'] = f'{gg}: Below stock ↑'
            
                if qq > stock['adj close'][-2] and qq > stock['open'][-2]:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Above stock ↑'
                else:
                    holdings_dict[symbol]['180_sma'] = f'{qq}: Below stock ↑'
            
            
            holdings_dict[symbol]['RSI'] = formatting(stock.get('rsi_13')[-1])
        except:
            print(f"Couldn't find symbol {symbol} in lookup table")
            pass
## ------------------------- Email ------------------------- ##
    
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
        #TODO: FI
        try:
            print(key)
            print(val['1M'])
            x.add_row([key, val['Current Holdings'], val['Current Average'], val['1M'], val['1W'], val['1D'], val['Today Open'], val['9_sma'], val['180_sma'], val['RSI']])
        except:
            print(f"Insufficient data {symbol}")
            pass
        
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
generate_holdings(all_holdings['Ticker Symbol'].tolist())

## Add watchlist for html table
generate_holdings(watchlist)

generate_rsi(all_holdings)

generate_rsi_watchlist(watchlist)

send_email(holdings_dict)

## ------------------------- Graphs ------------------------- ##

import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go
from datetime import timedelta

monthly_returns_df.index = monthly_returns_df.index.strftime('%Y-%m')
monthly_returns_df.reset_index(level=0, inplace=True)

# Monthly Returns and targets
fig = go.Figure(data=[
    go.Scatter(name='Target', x=summary_df['Date'], y=summary_df['Target']),
    go.Scatter(name='Minimun Goal', x=summary_df['Date'], y=[100 for x in range(len(summary_df['Date']))]),
    go.Bar(name='Return', x=monthly_returns_df['Date'], y=monthly_returns_df['Returns']),
])

# Change the bar mode
fig.update_layout(barmode='overlay', title='Monthly Returns and targets')
plot(fig)

# Cumsum
fig = px.bar(monthly_returns_df, x='Date', y='Returns', color='Date', title='Running Total Realised Returns')
plot(fig)

# Daily Returns
fig = px.bar(daily_returns_df, x='Date', y='Returns', color='Date', title='Daily Returns')
plot(fig)
## TODO: On click show all trades that day: daily_returns_df[daily_returns_df['Date'] == day_clicked]

# Dividends
fig = px.bar(summary_df, x='Date', y='Dividends', color='Date', title='Dividends')
plot(fig)

weekly_returns_df.index=weekly_returns_df.index.to_series().astype(str) # Change type period to string
weekly_returns_df.reset_index(level=0, inplace=True)
weekly_returns_df['Date'] = weekly_returns_df['Date'].str.split('/', 1).str[1] # Week ending

weekly_returns_df['Date'] = pd.to_datetime(weekly_returns_df['Date']) + timedelta(days=-2) # Last working day of week

# Weekly Returns
fig = px.bar(weekly_returns_df, x='Date', y='Returns', color='Date', title='Weekly Returns')
plot(fig)

# Buy/Sell
counts = portfolio['Type'].value_counts()       
counts_df = counts.reset_index()
counts_df.columns = ['Type', 'Count']
fig = px.pie(counts_df, values='Count', names='Type')
plot(fig)

## ------------------------- Tesla Portfolio Performance ------------------------- ##

index = web.DataReader('TSLA', 'yahoo', start, end)
index = index.reset_index()
fig = px.line(index, x="Date", y="Adj Close")
plot(fig)

tsla = portfolio[portfolio['Ticker Symbol'] == 'TSLA']

tsla['dolla'] = tsla['Price'] / tsla['Exchange rate']
tsla['Trading day'] = pd.to_datetime(tsla['Trading day']) # Match index data format

mask = (tsla['Trading day'] > datetime.datetime(2020, 2, 10)) & (tsla['Trading day'] <= datetime.datetime.now())

tsla = tsla.loc[mask]

fig = px.scatter(tsla, x='Trading day', y='Price', color='Type', title='Daily Returns')
plot(fig)

buys = tsla[tsla['Type']=='Buy']
sells = tsla[tsla['Type']=='Sell']

def transform_row(r):
    if r['Trading day'] <= datetime.datetime(2020, 8, 30): # Tesla 5 for 1 Stock split
        r.dolla = r.dolla/5
    return r

buys = buys.apply(transform_row, axis=1)
sells = sells.apply(transform_row, axis=1)

## Graph

fig = go.Figure()

## TODO: Allow user to switch between line and candlestick chart

# Add traces
fig.add_trace(go.Scatter(x=index['Date'], y=index['Adj Close'], 
                    mode='lines'))

# Buys
fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
                    mode='markers',
                    name='Buy point'
                    ))
# Sells
fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
                    mode='markers',
                    name='Sell point'
                    ))

fig.update_layout(title='Tesla Trading Activity')
plot(fig)

## Simple Candlestick
fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                open=index['Open'],
                high=index['High'],
                low=index['Low'],
                close=index['Adj Close'],
                name='Stock')])

fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
                    mode='markers',
                    name='Sell point',
                    #marker=dict(color='#ff7f0e')
                    marker=dict(size=7,
                                line=dict(width=2,
                                          color='DarkSlateGrey')),
                    ))

fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
                    mode='markers',
                    name='Buy point',
                    marker=dict(size=7,
                                line=dict(width=2,
                                          color='DarkSlateGrey')),
                    ))

fig.update_layout(hovermode="x unified", title='Tesla Stock Graph') # Currently plotly doesn't support hover for overlapping points in same trace

plot(fig)

## Stock activity - How many times I've bought/sold a stock         
stocks = portfolio['Ticker Symbol'].value_counts()         
stocks = stocks.reset_index()
stocks.columns = ['Ticker Symbol', 'Count']           
fig = px.pie(stocks, values='Count', names='Ticker Symbol', title='Portfolio Trading Activity')
plot(fig)

def chart(ticker):

    market = all_212_equities[all_212_equities['INSTRUMENT'] == ticker]['MARKET NAME'].values[0] 
            
    yf_symbol = get_yf_symbol(market, ticker)   
    
    start = datetime.datetime(2020, 2, 8)
    end = datetime.datetime.now()    
        
    index = web.DataReader(yf_symbol, 'yahoo', start, end)
    index = index.reset_index()
    
    df = portfolio[portfolio['Ticker Symbol'] == ticker]
    
    df['dolla'] = df['Price'] / df['Exchange rate']
    df['Trading day'] = pd.to_datetime(df['Trading day']) # Match index data format
    
    buys = df[df['Type']=='Buy']
    sells = df[df['Type']=='Sell']
    
    ## Candlestick Graph
        
    fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                    open=index['Open'],
                    high=index['High'],
                    low=index['Low'],
                    close=index['Adj Close'],
                    name='Stock')])
    
    fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
                        mode='markers',
                        name='Sell point',
                        #marker=dict(color='#ff7f0e')
                        marker=dict(size=7,
                                    line=dict(width=2,
                                              color='DarkSlateGrey')),
                        ))

    fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
                        mode='markers',
                        name='Buy point',
                        #marker=dict(color='#1f77b4')
                        marker=dict(size=7,
                                    line=dict(width=2,
                                              color='DarkSlateGrey')),
                        ))
    
    fig.update_layout(hovermode="x unified", title=f'{ticker} Buy/Sell points')
    
    plot(fig)

## Top 5 Portfolio Performance 

aaa = portfolio['Ticker Symbol'].value_counts().head()

for stock in aaa.index:
    chart(stock)

## ------------------------- Buy/Sell Performance ------------------------- ##

index['Midpoint'] = (index['High'] + index['Low']) / 2

buy_target = []
sell_target = []

for i, row in buys.iterrows():
    mid = index[index['Date'] == row['Trading day']]['Midpoint'].values[0]
    
    if row['dolla'] < mid:
        buy_target.append(1)
    else:
        buy_target.append(0)

for i, row in sells.iterrows():
    mid = index[index['Date'] == row['Trading day']]['Midpoint'].values[0]
    
    if row['dolla'] > mid:
        sell_target.append(1)
    else:
        sell_target.append(0)

buys['Target'] = buy_target
sells['Target'] = sell_target

# buy['Target'] = 
#buys.loc[buys['dolla'] < index[index['Date'] == buys['Trading day']]['Midpoint'].values[0], 'test'] = 1

## Continous colour graph https://plotly.com/python/discrete-color/

fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                open=index['Open'],
                high=index['High'],
                low=index['Low'],
                close=index['Adj Close'],
                name='Stock')])

fig1 = px.scatter(sells, x='Trading day', y='dolla', color='Target')
fig1.update_traces(marker=dict(size=7, line=dict(width=2, color='DarkSlateGrey')))
fig.add_trace(fig1.data[0])

fig2 = px.scatter(buys, x='Trading day', y='dolla', color='Target')
fig2.update_traces( marker=dict(size=7, line=dict(width=2, color='DarkSlateGrey')))
fig.add_trace(fig2.data[0])

fig.update_layout(hovermode="x unified", title='Tesla Stock Graph')

#fig.update_layout(coloraxis_showscale=False)

plot(fig)

## Discrete color graph

fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                open=index['Open'],
                high=index['High'],
                low=index['Low'],
                close=index['Adj Close'],
                name='Stock')])

# Must be a string for plotly to see it as a discrete value
sells['Target'] = sells['Target'].astype(str)
buys['Target'] = buys['Target'].astype(str)

fig1 = px.scatter(sells, x='Trading day', y='dolla', color='Target')
fig1.data[0].marker =  {'color':'#E24C4F', 'line': {'color': 'white', 'width': 2}, 'size': 7, 'symbol': 'circle'}
fig1.data[1].marker =  {'color':'#E24C4F', 'line': {'color': 'black', 'width': 2}, 'size': 7, 'symbol': 'circle'}
fig1.data[0].name = 'Successful Sell Point'
fig1.data[1].name = 'Unsuccessful Sell Point'
fig.add_trace(fig1.data[0])
fig.add_trace(fig1.data[1])

fig2 = px.scatter(buys, x='Trading day', y='dolla', color='Target')
#fig2.update_traces(marker=dict(color='blue'))
#fig2.update_traces(marker=dict(color='#30C296', size=7, line=dict(width=2, color='DarkSlateGrey')))
fig2.data[0].marker =  {'color':'#3D9970', 'line': {'color': 'white', 'width': 2}, 'size': 7, 'symbol': 'circle'}
fig2.data[1].marker =  {'color':'#3D9970','line': {'color': 'black', 'width': 2}, 'size': 7, 'symbol': 'circle'}
fig2.data[0].name = 'Successful Buy Point'
fig2.data[1].name = 'Unsuccessful Buy Point'
fig.add_trace(fig2.data[0])
fig.add_trace(fig2.data[1])

# fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
#                     mode='markers',
#                     name='Sell point',
#                     color='Target' 
#                     ))

# fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
#                     mode='markers',
#                     name='Buy point',
#                     marker=dict(color='Target')
#                     ))

fig.update_layout(hovermode="x unified", title='Tesla Stock Graph')

plot(fig)

a = buys['Target'].value_counts()
b = sells['Target'].value_counts()
count = a.add(b,fill_value=0)

## ------------------------- Facebook Prophet ------------------------- ##
    
from fbprophet import Prophet

model = Prophet()

end = datetime.datetime.now()
start = datetime.datetime(end.year - 5, end.month, end.day) # Annual avg return is usually based on 5 year historical market performance

df = web.DataReader('^VIX', 'yahoo', start, end)
df = df.reset_index()

# Have to rename columns for fbprophet
# Dataframe must have columns "ds" and "y" with the dates and values respectively.

df[['ds', 'y']] = df[['Date', 'Adj Close']]

model.fit(df)

future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

model.plot(forecast)

trace = go.Scatter(
    name = 'Actual price',
    mode = 'markers',
    x = list(forecast['ds']),
    y = list(df['y']),
)

trace1 = go.Scatter(
    name = 'trend',
    mode = 'lines',
    x = list(forecast['ds']),
    y = list(forecast['yhat']),
    marker=dict(
        #color='blue',
        line=dict(width=3)
    )
)

upper_band = go.Scatter(
    name = 'upper band',
    mode = 'lines',
    x = list(forecast['ds']),
    y = list(forecast['yhat_upper']),
    #line= dict(color='#57b88f'),
    fill = 'tonexty'
)

lower_band = go.Scatter(
    name= 'lower band',
    mode = 'lines',
    x = list(forecast['ds']),
    y = list(forecast['yhat_lower']),
    #line= dict(color='red')
)

data = [ trace1, lower_band, upper_band, trace]

layout = dict(title='Stock Price Estimation Using FbProphet',
             xaxis=dict(title = 'Dates', ticklen=2, zeroline=True))

figure=dict(data=data,layout=layout)

plot(figure)














            
            