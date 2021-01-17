# -*- coding: utf-8 -*-
"""
Created on Sat Jan 16 11:48:24 2021

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
from helpers import get_buy_sell, get_yf_symbol, time_frame_returns

load_dotenv(verbose=True, override=True)

db_URI = os.getenv('AWS_DATABASE_URL')
engine = create_engine(db_URI)

def chart(ticker):
    
    all_212_equities = pd.read_sql_table("equities", con=engine, index_col='index')

    
    market = all_212_equities[all_212_equities['INSTRUMENT'] == ticker]['MARKET NAME'].values[0] 
    
    buys, sells = get_buy_sell(ticker)
    
    start = datetime(2020, 2, 7)
    end = datetime.now()    
        
    yf_symbol = get_yf_symbol(market, ticker)   
    
    index = web.DataReader(yf_symbol, 'yahoo', start, end)
    index = index.reset_index()
    
    averages_df = averages[averages['Ticker Symbol'] == ticker]
    averages_df['ISIN'] = all_holdings[all_holdings['Ticker Symbol'] == ticker]['ISIN'].values[0]
    averages_df = averages_df.apply(avg_stock_split_adjustment, axis=1)

    # ## TODO: Allow user to switch between line and candlestick chart

    # # Add traces
    # fig.add_trace(go.Scatter(x=index['Date'], y=index['Adj Close'], 
    #                     mode='lines'))
    
    # # Buys
    # fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
    #                     mode='markers',
    #                     name='Buy point'
    #                     ))
    # # Sells
    # fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
    #                     mode='markers',
    #                     name='Sell point'
    #                     ))
    
    ## Candlestick Graph
        
    fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                    open=index['Open'],
                    high=index['High'],
                    low=index['Low'],
                    close=index['Adj Close'],
                    name='Stock')])
    
    # Buys
    fig.add_trace(go.Scatter(x=sells['Trading day'], y=sells['dolla'],
                        mode='markers',
                        name='Sell point',
                        #marker=dict(color='#ff7f0e')
                        marker=dict(size=7,
                                    line=dict(width=2,
                                              color='DarkSlateGrey')),
                        ))
    
    # Sells
    fig.add_trace(go.Scatter(x=buys['Trading day'], y=buys['dolla'],
                        mode='markers',
                        name='Buy point',
                        #marker=dict(color='#1f77b4')
                        marker=dict(size=7,
                                    line=dict(width=2,
                                              color='DarkSlateGrey')),
                        ))
    
    # shapes = list()
    # for i in (20, 40, 60):
    #     shapes.append({'type': 'line',
    #                    'xref': 'x',
    #                    'yref': 'y',
    #                    'x0': ,
    #                    'y0': 0,
    #                    'x1': i,
    #                    'y1': 1})
    
    def hlines(r):
        fig.add_hline(y=r['Average']/r['Exchange rate'], line_width=3, line_dash="dash")

    averages_df[-5:-1].apply(hlines, axis=1)
    
    if index.iloc[-1]['Adj Close'] > averages_df.iloc[-1]['Average']/averages_df.iloc[-1]['Exchange rate']:
        fig.add_hline(y=averages_df.iloc[-1]['Average']/averages_df.iloc[-1]['Exchange rate'], line_width=3, line_dash="dash", line_color="green")
    else:
        fig.add_hline(y=averages_df.iloc[-1]['Average']/averages_df.iloc[-1]['Exchange rate'], line_width=3, line_dash="dash", line_color="red")

    fig.update_layout(hovermode="x unified", title=f'{ticker} Buy/Sell points') # Currently plotly doesn't support hover for overlapping points in same trace
    
    return fig


def performance_chart(ticker):

    all_212_equities = pd.read_csv('stock_list.csv')
    
    market = all_212_equities[all_212_equities['INSTRUMENT'] == ticker]['MARKET NAME'].values[0] 
    
    buys, sells = get_buy_sell(ticker) 
    
    start = datetime(2020, 2, 7)
    end = datetime.now()    
    
    yf_symbol = get_yf_symbol(market, ticker)   
    
    index = web.DataReader(yf_symbol, 'yahoo', start, end)
    index = index.reset_index()
    
    index['Midpoint'] = (index['High'] + index['Low']) / 2
    
    buy_target = []
    sell_target = []
    
    for i, row in buys.iterrows():
        mid = index[index['Date'] == row['Trading day']]['Midpoint'].values[0]
        
        if row['Execution_Price'] < mid:
            buy_target.append(1)
        else:
            buy_target.append(0)
    
    for i, row in sells.iterrows():
        mid = index[index['Date'] == row['Trading day']]['Midpoint'].values[0]
        
        if row['Execution_Price'] > mid:
            sell_target.append(1)
        else:
            sell_target.append(0)
    
    buys['Target'] = buy_target
    sells['Target'] = sell_target
    
    ## Discrete color graph
    
    fig = go.Figure(data=[go.Candlestick(x=index['Date'],
                    open=index['Open'],
                    high=index['High'],
                    low=index['Low'],
                    close=index['Adj Close'],
                    name='Stock')])
    
    # Must be a string for plotly to interpret numeric values as a discrete value
    # https://plotly.com/python/discrete-color/
    sells['Target'] = sells['Target'].astype(str)
    buys['Target'] = buys['Target'].astype(str)
    
    fig1 = px.scatter(sells, x='Trading day', y='Execution_Price', color='Target')
    fig1.data[0].marker =  {'color':'#E24C4F', 'line': {'color': 'yellow', 'width': 2}, 'size': 7, 'symbol': 'circle'}
    fig1.data[1].marker =  {'color':'#E24C4F', 'line': {'color': 'black', 'width': 2}, 'size': 7, 'symbol': 'circle'}
    fig1.data[0].name = 'Successful Sell Point'
    fig1.data[1].name = 'Unsuccessful Sell Point'
    fig.add_trace(fig1.data[0])
    fig.add_trace(fig1.data[1])
    
    fig2 = px.scatter(buys, x='Trading day', y='Execution_Price', color='Target')
    #fig2.update_traces(marker=dict(color='blue'))
    #fig2.update_traces(marker=dict(color='#30C296', size=7, line=dict(width=2, color='DarkSlateGrey')))
    fig2.data[0].marker =  {'color':'#3D9970', 'line': {'color': 'yellow', 'width': 2}, 'size': 7, 'symbol': 'circle'}
    fig2.data[1].marker =  {'color':'#3D9970','line': {'color': 'black', 'width': 2}, 'size': 7, 'symbol': 'circle'}
    fig2.data[0].name = 'Successful Buy Point'
    fig2.data[1].name = 'Unsuccessful Buy Point'
    fig.add_trace(fig2.data[0])
    fig.add_trace(fig2.data[1])
    
    fig.update_layout(hovermode="x unified", title=f'{ticker} Stock Graph', 
                      legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                    ))
    
    return fig

# Monthly Returns and targets
def goal_chart():
    
    summary_df = pd.read_sql_table("summary", con=engine, index_col='index')
    
    fig = go.Figure(data=[
        go.Scatter(name='Target', x=summary_df['Date'], y=summary_df['Target']),
        go.Scatter(name='Minimum Target', x=summary_df['Date'], y=summary_df['Minimum Goal']),
        go.Bar(name='Return', x=summary_df['Date'], y=summary_df['Returns']),
        go.Scatter(name='Goal', x=summary_df['Date'], y=summary_df['Goal']),
        go.Scatter(name='House Goal', x=summary_df['Date'], y=summary_df['House Goal']),
    ])
    
    # Change the bar mode
    fig.update_layout(barmode='overlay', title='Monthly Returns and targets')
    
    return fig

# Cumsum
def cumsum_chart():
    monthly_returns_df = pd.read_sql_table("summary", con=engine, index_col='index')
    monthly_returns_df['Rolling Returns'] = monthly_returns_df['Returns'].cumsum()
    fig = px.bar(monthly_returns_df, x='Date', y='Rolling Returns', title='Rolling Realised Returns')
    return fig

def dividend_chart():
    # Dividends
    summary_df = pd.read_sql_table("summary", con=engine, index_col='index')
    fig = px.bar(summary_df, x='Date', y='Dividends', color='Date', title='Dividends')
    return fig

def period_chart(time='M'):
        
    timeframe_returns_df = time_frame_returns(time)
    timeframe_returns_df.reset_index(level=0, inplace=True)

    if time == 'W':
        timeframe_returns_df.Date = timeframe_returns_df.Date.astype(str) # Change type period to string
        timeframe_returns_df['Date'] = timeframe_returns_df['Date'].str.split('/', 1).str[1] # Week ending
        timeframe_returns_df['Date'] = pd.to_datetime(timeframe_returns_df['Date']) + timedelta(days=-2) # Last working day of week

    if time == 'M' or time == 'Q':
        timeframe_returns_df['Date'] = timeframe_returns_df['Date'].dt.strftime('%m-%Y')
    elif time == 'A-APR'or time == 'Y':
        timeframe_returns_df['Date'] = timeframe_returns_df['Date'].dt.strftime('%Y')
    else:
        timeframe_returns_df['Date'] = timeframe_returns_df['Date'].dt.strftime('%d-%m-%Y')

    fig = px.bar(timeframe_returns_df, x='Date', y='Returns', color='Date', title='Returns')
    
    return fig

def profit_loss_chart():
    # P/L
    monthly_returns_df = pd.read_sql_table("summary", con=engine, index_col='index')
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_returns_df['Date'], y=monthly_returns_df['Gains'],
                    marker_color='green',
                    name='Gains'))
    fig.add_trace(go.Bar(x=monthly_returns_df['Date'], y=monthly_returns_df['Losses'],
                    base=0,
                    marker_color='crimson',
                    name='Losses'
                    ))
    fig.update_layout(barmode='overlay')
    return fig

# # Daily Returns
# fig = px.bar(daily_returns_df, x='Date', y='Returns', color='Date', title='Daily Returns')
# plot(fig)

# ## TODO: On click show all trades that day: daily_returns_df[daily_returns_df['Date'] == day_clicked]

# # Buy/Sell
# counts = trades['Type'].value_counts()       
# counts_df = counts.reset_index()
# counts_df.columns = ['Type', 'Count']
# fig = px.pie(counts_df, values='Count', names='Type')
# plot(fig)

# ## Stock activity - How many times I've bought/sold a stock         
# stocks = trades['Ticker Symbol'].value_counts()         
# stocks = stocks.reset_index()
# stocks.columns = ['Ticker Symbol', 'Count']           
# fig = px.pie(stocks, values='Count', names='Ticker Symbol', title='Portfolio Trading Activity')
# plot(fig)

def avg_stock_split_adjustment(r):
        
    market = get_market(r['ISIN'], r['Ticker Symbol'])[1] 
    
    ticker = get_yf_symbol(market, r['Ticker Symbol'])
    
    aapl = yf.Ticker(ticker)
    split_df = aapl.splits.reset_index()
    split = split_df[split_df['Date'] > r['Trading day']]['Stock Splits'].sum()
    
    if split > 0:
        r.Average = r.Average/split
    
    return r

















def ml_model():
    pytrend = TrendReq()

    keyword = 'tesla Stock'
    
    end = datetime.now()
    start = datetime(end.year - 5, end.month, end.day)
    
    ss = start.strftime('%Y-%m-%d')
    ee = end.strftime('%Y-%m-%d')
    
    # 1 year follows price trend better than 5 year 
    # This  may be because the values are calculated on a scale from 0 to 100, 
    # where 100 is the timeframe with the most popularity as a fraction of total searches in the given period of time, 
    # a value of 50 indicates a time which is half as popular. 
    # A value of 0 indicates a location where there was not enough data for this term. 
    # Source →Google Trends.
    
    # For my hypothesis I feel 1 year is more accurate due to influx of new traders due to corona
    # Old school traders rely on fundementals/technicals whereas newer trader trade on sentiment and momentum
    
    pytrend.build_payload(kw_list=[keyword], timeframe=f'{ss} {ee}')
    df = pytrend.interest_over_time() # Weekly data
    df.reset_index(level=0, inplace=True)
    
    df2 = dailydata.get_daily_data(keyword, start.year, start.month, end.year, end.month)
    df2.reset_index(level=0, inplace=True)
    df2 = df2.rename(columns={'date':'Date'})
    
    index = web.DataReader('tsla', 'yahoo', start, end)
    index = index.reset_index()

    merged_df = pd.merge(index, df2, on="Date")

    model_df = merged_df[['Date', 'Open', 'Adj Close', 'Volume', merged_df.filter(regex='_unscaled$').columns[0]]]

    training_dataset = model_df[model_df['Date'] < datetime(2020, 11, 1)]
    test_data = model_df[model_df['Date'] >= datetime(2020, 11, 1)]
    
    from sklearn.preprocessing import MinMaxScaler
    import numpy as np
    
    ## Using normalisation as will be using sigmoid function as activation functionn of output layer
    sc = MinMaxScaler()
    training_data = sc.fit_transform(training_dataset.drop(['Date'], axis=1))
    training_data.shape[0]
    
    window = 30
    
    x_train = [training_data[i-window:i] for i in range(60, training_data.shape[0])]
    
    # Open stock price
    y_train = [training_data[i, 0] for i in range(60, training_data.shape[0])]
    
    x_train, y_train = np.array(x_train ),  np.array(y_train)
    
    x_train.shape, y_train.shape
    
    from keras.models import Sequential
    from keras.layers import LSTM, Dense, Dropout
    
    ## Model architecture
    model = Sequential()
    
    ## Chose 50 nodes for high dimensionality
    model.add(LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])))
    
    # Dropout Regularisation to pervent overfitting. 20% is a common choice
    model.add(Dropout(0.2))
    
    # Layers 2 - 3
    for x in range(2,4):
        print(f'Initalise layer {x}')
        model.add(LSTM(50, return_sequences=True))
        model.add(Dropout(0.2))
    
    # Final layer
    model.add(LSTM(50))
    model.add(Dropout(0.2))
    
    # Output layer
    model.add(Dense(1))
    
    model.compile(loss="mean_squared_error", optimizer="adam") # Try RMWprop optimizer after
    
    model.summary()
    
    ## 32 recommended batch size
    model.fit(
        x_train, y_train, epochs=100, batch_size=32, verbose=1, validation_split=0.2 #, validation_data=(Xtest, ytest)
    ) # Loss progressively got better (lower)
    
    ## https://machinelearningmastery.com/how-to-use-the-timeseriesgenerator-for-time-series-forecasting-in-keras/
    
    ## Predictions ##
    
    #stock_test_data = model_df[model_df.index >= len(training_data)]
    #dataset = model_df.drop(['Date'], axis=1)
    
    # Adding last window days of training set to test set for LSTM
    total_test_data = pd.concat((training_dataset.tail(window), test_data), ignore_index = True).drop(['Date'], axis=1)
    
    scaled_test_data = sc.transform(total_test_data)
    
    #stock_test_data = test_data.drop(['Date'], axis=1)
    
    x_test = [scaled_test_data[i-window:i] for i in range(window, scaled_test_data.shape[0])]
    y_test = [scaled_test_data[i, 0] for i in range(window, scaled_test_data.shape[0])]
    
    x_test, y_test = np.array(x_test),  np.array(y_test)
    
    x_test.shape, y_test.shape
    
    y_pred = model.predict(x_test)
    
    ## How to use inverse_transform in MinMaxScaler for a column in a matrix
    ## https://stackoverflow.com/questions/49330195/how-to-use-inverse-transform-in-minmaxscaler-for-a-column-in-a-matrix
    # invert predictions
    # Original scaler variable (sc) won't work as it expects a 2D array instead of the 1D y_pred array we are trying to parse.
    scale = MinMaxScaler()
    scale.min_, scale.scale_ = sc.min_[0], sc.scale_[0]
    y_pred = scale.inverse_transform(y_pred)
    y_test = test_data['Open']
    
    y_pred  = [x[0] for x in y_pred.tolist()]
    
    test_dates = pd.Series([training_dataset['Date'].iloc[-1]]).append(test_data['Date'], ignore_index=True)
    y_pred_graph =  [training_dataset['Open'].iloc[-1]] + y_pred
    y_test_graph = pd.Series([training_dataset['Open'].iloc[-1]]).append(y_test, ignore_index=True).tolist()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=training_dataset['Date'], y=training_dataset['Open'], name='Past Stock Price'))
    fig.add_trace(go.Scatter(x=test_dates, y=y_pred_graph, name='Predicted Stock Price'))
    fig.add_trace(go.Scatter(x=test_dates, y=y_test_graph, name='Actual Stock Price'))
    fig.update_layout(title="Predicted vs Actual Stock Price", xaxis_title="Date", yaxis_title="Opening Price")
    
    return fig