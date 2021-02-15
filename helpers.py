# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 13:05:52 2020

@author: david
"""
import imaplib
import os
import email
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import stockstats
import collections
from pandas_datareader import data as web
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from prettytable import PrettyTable
import re
import yfinance as yf
from datetime import datetime, timedelta
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go
from pytrends.request import TrendReq
from sqlalchemy import create_engine
from pytrends import dailydata
from forex_python.converter import CurrencyRates
import glob

load_dotenv(verbose=True, override=True)

email_user = os.getenv('GMAIL')
email_pass = os.getenv('GMAIL_PASS') # Make sure 'Less secure app access' is turned on

c = CurrencyRates()

port = 993

SMTP_SERVER = "imap.gmail.com"

mail = imaplib.IMAP4_SSL(SMTP_SERVER)

mail.login(email_user, email_pass)

db_URI = os.getenv('AWS_DATABASE_URL')

engine = create_engine(db_URI)

# date = '28/01/2021 14:42'
# date_time_obj = datetime.strptime(date, '%d/%m/%Y %H:%M')
# rate = c.get_rate('USD', 'GBP', date_time_obj)

# def get_ex_rate(r):
#     date_time_obj = datetime.strptime(date, '%d/%m/%Y %H:%M')
#     rate = c.get_rate(r['Currency (Price / share)'], 'GBP', date_time_obj)
#     r['Exchange rate'] = rate
    
# missing_data.apply(get_rate, axis=1)

def get_mailbox_list(folder):
    
    mail.select(folder)

    status, mailbox = mail.search(None, 'ALL')
        
    mailbox_list = mailbox[0].split()
    
    return mailbox_list

def get_portfolio():
    
    print('Updating Orders')
    
    mailbox_list = get_mailbox_list('investing')
    
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
        
    trades = pd.DataFrame(data, columns=column_headers)
    
    float_values = ['Shares', 'Price', 'Total amount','Commission', 'Charges and fees','Total cost', 'Exchange rate']

    for column in float_values:
        trades[column] = trades[column].str.rstrip('GBP').astype(float)
    
    ## Split ISIN and stock, need ISIN because some companies have the same ticker symbol, ISIN is the uid
    trades[['Ticker Symbol', 'ISIN']] = trades['Ticker Symbol'].str.split('/', expand=True)
    
    ## TODO: Temp fix by changing DTG to Jet2, Dartgroup changed their ticker symbol to JET2
    trades.replace('DTG','JET2', inplace=True)
    
    ## Airbus changed their ticker symbol
    trades['Ticker Symbol'].replace('AIRp', 'AIR', inplace=True)
    
    trades['Trading day'] = pd.to_datetime(trades['Trading day'], format='%d-%m-%Y', dayfirst=True) #pd.to_datetime(trades["Trading day"]).dt.strftime('%m-%d-%Y')
    
    ## For getting ROI, Dataframe needs to be ordered in ascending order and grouped by Ticker Symbol
    trades.sort_values(['Ticker Symbol','Trading day','Trading time'], inplace=True, ascending=True)
    
    trades['Execution_Price'] = trades['Price'] / trades['Exchange rate']
    
    ## Datetime not compatible with excel
    #trades['Trading day'] = pd.to_datetime(trades['Trading day'], dayfirst=True)
    
    ## Look into combining tickers using code like this 
    ## gb.loc[gb["geo_code"]=="E41000052",'geo_code'] = "E06000052" (Visual Analytics Week 7 lab007)
    
    '''
    Things to take note when creating a Transactions Portfolio for Simply Wall St:
    
    For stocks that have a currency other than your portfolio’s base currency, the entry should be based on the original listing currency. 
    The system will automatically convert it to the currency you have chosen for your portfolio. 
    If you enter a converted price, it will create a wrong converted value, as if the value will be converted twice. 
    
    https://support.simplywall.st/hc/en-us/articles/360001480916-How-to-Create-a-Portfolio
    
    '''
    
    # simply_wall_st = trades.filter(['Ticker Symbol', 'Trading day', 'Shares', 'Price', 'Total amount', 'Type', 'Exchange rate'], axis=1)
    
    # #simply_wall_st['Total amount'] = simply_wall_st['Total amount'].astype(float)
    # # simply_wall_st['Exchange rate'] = simply_wall_st['Exchange rate'].astype(float)
    # # simply_wall_st['Price'] = simply_wall_st['Price'].astype(float)
    
    # 
    # simply_wall_st['Exchange rate'] = simply_wall_st['Exchange rate'].replace(0.01, 1)
    # simply_wall_st['Price'] = simply_wall_st['Price'] / simply_wall_st['Exchange rate']
    
    # simply_wall_st.to_csv('Simply Wall St Portfolio.csv', index=False)
    
    ## ------------------------- Add missing data from csv ------------------------- ##

    data = pd.DataFrame()
    for file_name in glob.glob('missing_data/'+'*.csv'):
        x = pd.read_csv(file_name, low_memory=False)
        print(file_name)
        data = pd.concat([data,x],axis=0)

    data['Execution_Price'] = data['Price / share']
    data[['Trading day', 'Trading time']] = data['Time'].str.split(' ', expand=True)
    data['Type'] = data['Action'].str.split(' ').str[1].str.capitalize()
    data['Trading day'] = pd.to_datetime(data['Trading day'])
    data['Price'] = data['Price / share'] / data['Exchange rate']
    
    data.drop(['Time', 'Action', 'Finra fee (GBP)', 'Currency (Price / share)', 'Result (GBP)', 'Price / share', 'Name' ], inplace=True, axis=1)  
    
    data.rename(columns={'Ticker':'Ticker Symbol', 'No. of shares':'Shares', 'Total (GBP)':'Total amount', 'ID':'Order ID',
                                  'Finra fee (GBP)':'Charges and fees', 'Currency (Price / share)': 'Currency Price / share',
                                  'Result (GBP)':'Result'}, inplace=True)
    
    trades = pd.concat([trades, data], ignore_index=True)
    trades.sort_values(['Ticker Symbol','Trading day','Trading time'], inplace=True, ascending=True)

    trades.to_csv('Investment trades.csv', index=False )
    trades.to_sql('trades', engine, if_exists='replace')
    
    print('Orders Updated')
    
    return trades

#get_portfolio()

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
    elif symbol == 'IAG':
        """
        Works assuming I never buy IAMGold Corporation (IAG)
        International Consolidated Airlines Group SA in equities df 
        whereas IAG SA in holdings so string match doesn't work
        """
        yf_symbol = 'IAG.L'  
    else:
        yf_symbol = symbol
    return yf_symbol

def get_market(isin, symbol, old_symbol=''):
    
    ## When tickers change (due to mergers or company moving market) 212 removes the old ticker from the equities table
    ## As 212 doesn't provide the company name in the daily statement there is no way for me to link old tickers with the new one
    ## so will manually replace tickers here
    ## Preventing this in the future by saving all old tickers in a csv
    all_212_equities = pd.read_sql_table("equities", con=engine, index_col='index')

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
    return old_symbol, market

def stock_split_adjustment(r):
        
    market = get_market(r['ISIN'], r['Ticker Symbol'])[1] 
    
    ticker = get_yf_symbol(market, r['Ticker Symbol'])
    
    aapl = yf.Ticker(ticker)
    split_df = aapl.splits.reset_index()
    split = split_df[split_df['Date'] > r['Trading day']]['Stock Splits'].sum()
    
    if split > 0:
        r.Execution_Price = r.Execution_Price/split
    
    return r

def time_frame_returns(timeframe='M'):
    
    returns_df = pd.read_sql_table("returns", con=engine, index_col='index', parse_dates=['Dates'])
    
    # Fill missing business days
    idx = pd.bdate_range(min(returns_df.Date), max(returns_df.Date))
    returns_df.set_index('Date', inplace=True)
    #s.index = pd.DatetimeIndex(s.index)
    daily_returns_df = returns_df.reindex(idx, fill_value=0).reset_index().rename(columns={'index':'Date'})
    
    """ 
    Time Frames
    # Yearly Returnsn "Y"

    # Quaterly Returns "Q"
    
    # Tax year "A-APR" https://stackoverflow.com/questions/35339139/where-is-the-documentation-on-pandas-freq-tags
    
    # Monthly Returns "M"
    
    # Weekly Returns "W"
    """
    
    period = daily_returns_df.Date.dt.to_period(timeframe)
    g = daily_returns_df.groupby(period)
    timeframe_returns_df = g.sum()

    return timeframe_returns_df

def get_summary():

    mailbox_list = get_mailbox_list('dividends')
    
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
    
    now = datetime.now()

    summary_df.loc[len(summary_df)] = [f"{now.year}-{now.strftime('%m')}" , float('NaN'), summary_df.loc[len(summary_df)-1]['Closing balance'], float('NaN')]
     
    summary_df['Target'] = summary_df['Opening balance'] * .05 # Aim for 5% returns a month
    
    summary_df['Goal'] = summary_df['Opening balance'] * .10
    
    monthly_returns_df = time_frame_returns()
    
    monthly_returns_df.index = monthly_returns_df.index.strftime('%Y-%m')
    monthly_returns_df.reset_index(level=0, inplace=True)
    
    summary_df = summary_df.merge(monthly_returns_df, on='Date')
    
    month_count = pd.to_datetime(summary_df['Date'], errors='coerce').dt.year.value_counts()
    
    summary_df['House Goal'] = [float('NaN') for x in range(month_count.values[0])] + [1000 for x in range(month_count.values[1:].sum())]  
    summary_df['Minimum Goal'] = [100 for x in range(month_count.values[0])] + [200 for x in range(month_count.values[1:].sum())]
    
    summary_df.to_sql('summary', engine, if_exists='replace')
    summary_df.to_csv('Monthly Summary.csv', index=False )
    
    return summary_df

def get_buy_sell(ticker):
    
    portfolio = pd.read_sql_table("trades", con=engine, index_col='index', parse_dates=['Trading day'])
    
    df = portfolio[portfolio['Ticker Symbol'] == ticker]

    #df['Execution_Price'] = df['Price / share'] # Convert price to original currency
    # df['Execution_Price'] = df['Price'] / df['Exchange rate'] # for emails instead of csv
    
    df['Trading day'] = pd.to_datetime(df['Trading day']) # Match index date format
    
    buys = df[df['Type']=='Buy']
    sells = df[df['Type']=='Sell']
    
    buys = buys.apply(stock_split_adjustment, axis=1)
    sells = sells.apply(stock_split_adjustment, axis=1)
    
    return buys, sells

def formatting(num):
    return round(num, 2)

def get_capital():
    
    mailbox_list = get_mailbox_list('deposits')
    
    total = 0
    
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
                
                #a = soup.find("strong").string
    
                table = soup.find_all('table')
    
                a = pd.read_html(str(table))[2][1][0]
                
                a = a.strip('GBP ')
                
                pattern = re.compile(r'\s+')
                a = re.sub(pattern, '', a)
                #print(a)
                total += float(a)
    
    # (9.2 from free shares, 85.2 from rbg rights issue)
    # Add this to match T212 total
    deposits = total + 94.4 
    
    total = 0
    
    mailbox_list = get_mailbox_list('withdraws')
    
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
                
                a = soup.find("span").string
                
                a = a.strip('GBP ')
                
                pattern = re.compile(r'\s+')
                a = re.sub(pattern, '', a)
                #print(a)
                total += float(a)
                
    #Add 85.2 for rbg rights issue to match T212
    withdraws = total + 85.2
    
    capital = round(deposits - withdraws, 2)

    return capital

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

def generate_rsi(all_holdings):
        
    for row in all_holdings.iloc:
    
        symbol = row[0]
        isin = row[1] ## Used in dataframe query, do not delete
        old_symbol = ''
        
        try:
            
            # print(symbol)
            # print(isin)
                
            old_symbol, market = get_market(isin, symbol)

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

# ## Current holdings in portfolio
# generate_holdings(all_holdings['Ticker Symbol'].tolist())

# ## Add watchlist for html table
# generate_holdings(watchlist)

# generate_rsi(all_holdings)

# generate_rsi_watchlist(watchlist)

# send_email(holdings_dict)









