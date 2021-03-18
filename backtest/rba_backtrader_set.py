# -*- coding: utf-8 -*-
"""Retrieves and backtests data and outputs for Dash app

Uses get_crypto_data to retrieve data from api or from
local database. Uses backtrader to test the data. Formats
that backtrader backtest result data into a format that
is consumable by the Dash app. The entire purpose of
this class is to bridge the backtrader data to the Dash
app.

Created on Sun Feb 21 18:05:42 2021

@author: Avery

"""

import backtrader as bt
from backtrader.utils import num2date
import rba_tools as rba
import rba_tools.retriver.get_crypto_data as gcd
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dateutil import parser

class MaCrossStrategy(bt.Strategy):

    def __init__(self):
        ma_fast = bt.ind.SMA(period = 10)
        ma_slow = bt.ind.SMA(period = 50)

        self.crossover = bt.ind.CrossOver(ma_fast, ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()

class backtrader_set():

    def __init__(self, symbols, strategy, sizer, sizer_param, start_date_str, end_date_str, exchange=None, starting_cash=1000.0):
        """
        Creates a backtrader_set instance for retriving, running analysis, and displaying results
        
        Parameters:
            symbols (list or str) -- symbols to run over
            strategy (backtrader.analyzers.Analyzer) -- backtrader strategy to run on the data
            sizer (bt.sizers.*) -- backtrader sizer to define size of trades
            sizer_param (any) -- parameter for sizer
            start_date_str (str) -- start date of analysis time period as a string
            end_date_str (str) -- end date of analysis time period as a string
            exchange (ccxt class) -- ccxt exchange to retrieve data from. Default is binance
            starting_cash (float) -- starting broker cash
        """
        if type(symbols) == str:
            symbols = [symbols]
        self.symbol_list = symbols

        self.strategy = strategy
        self.start_date_str = start_date_str
        self.end_date_str = end_date_str

        if exchange:
            self.exchange = exchange
        else:
            self.exchange = gcd.getBinanceExchange()
        
        self.starting_cash = starting_cash

        self.cerebro_list = []
        self.cerebro_return_list = []
        
        

    def run(self):
        """runs strategy over all symbols"""
        ohlcv_df_list = gcd.get_DataFrame(self.symbol_list, self.exchange, self.start_date_str, self.end_date_str, ret_as_list=True, timeframe='1d')
        for index in range(len(self.symbol_list)):
            cerebro = bt.Cerebro()
            data = bt.feeds.PandasData(dataname=ohlcv_df_list[index], nocase=True)
            cerebro.adddata(data)
            cerebro.addstrategy(self.strategy)

            cerebro.broker.setcash(self.starting_cash)

            self.cerebro_list.append(cerebro)
            self.cerebro_return_list.append(cerebro.run())
            


    def get_app_layout(self):
        return html.Div(children=[
            html.H1(children='Hello Dash'),

            html.Div(children='''
                Dash: A web application framework for Python.
                
            '''),

            dcc.Graph(
                id='example-graph',
                figure=self.fig
            )
        ])
    
def get_trades_from_cerebro_run(cerebro_run):
    #get trades. Arrays of this oberserver are double length for some reason
    array_list = []
    for strat in cerebro_run[0].stats:
        if isinstance(strat, bt.observers.trades.Trades):
            for line in strat.lines:
                pnl_data = np.frombuffer(line.array)
                np.nan_to_num(pnl_data, copy=False, nan=0)
                array_list.append(pnl_data)
    summed_ary = sum(array_list)
    summed_ary[summed_ary == 0] = np.nan
    return summed_ary[:int(len(summed_ary) / 2)] #not sure what the deal is with the double sized array but this seems to work
        
def get_pos_analysis(cerebro_run):
    #gets the PositionsValue analyzer. Raises IndexError if none or more than one found
    analysis = None
    count = 0
    for analyzer in cerebro_run[0].analyzers:
        if isinstance(analyzer, bt.analyzers.PositionsValue):
            count += 1
            analysis = analyzer.get_analysis().copy()
    if count > 1:
        raise IndexError('Multiple PositionsValue analyzers found')
    if analysis is None:
        raise IndexError('PositionsValue not found')
    return analysis

def get_cash_including_position(cerebro_run):
    #this assumes that PositionsValue analyzer exists with parameter cash=True (this is not the default) and headers=False (this is the default)
    pos_analysis = get_pos_analysis(cerebro_run)
    data = []
    for value in pos_analysis.values():
        data.append(sum(value))
    return np.round_(np.array(data),2)

def get_percent_cash_change(cerebro_run, decimals=2):
    cash_vals = get_cash_including_position(cerebro_run)
    start_val = cash_vals[0]
    return np.round((cash_vals / start_val - 1) * 100, decimals)

def get_datetime_array(cerebro_run):
    #retrieves a numpy array of datetime objects for the backtested time period
    datetime_as_float_ary = cerebro_run[0].lines.datetime.plot()
    datetime_obj_list = [num2date(float_date) for float_date in datetime_as_float_ary]
    return np.array(datetime_obj_list)

def get_buy_sell_from_cerebro_run(cerebro_run, trade_type='buy'):
    #get executed buy or sell orders. type can switch between buy and sell
    data = None
    for strat in cerebro_run[0].getobservers():
        if isinstance(strat, bt.observers.buysell.BuySell):
            line = 0 if trade_type == 'buy' else 1
            data = np.frombuffer(strat.lines[line].array)
    return data[:int(len(data) / 2)] #not sure what the deal is with the double sized array but this seems to work

def get_ohlcv_data_from_cerebro_run(cerebro_run):
    #get ohlcv dataframe from the data in the run
    data = cerebro_run[0].datas[0]
    start = 0
    end = len(data)
    return pd.DataFrame({
        'Open' : data.open.plotrange(start,end),
        'High' : data.high.plotrange(start,end),
        'Low' : data.low.plotrange(start,end),
        'Close' : data.close.plotrange(start,end),
        'Volume' : data.volume.plotrange(start,end)
        })

def summarize_cerebro_run(cerebro_run):
    #get pandas dataframe of summarized data
    index = get_datetime_array(cerebro_run)
    ohlcv_df = get_ohlcv_data_from_cerebro_run(cerebro_run)
    data = { 'Open' :ohlcv_df['Open'].values,
             'High' : ohlcv_df['High'].values,
             'Low' : ohlcv_df['Low'].values,
             'Close' : ohlcv_df['Close'].values,
             'Volume' : ohlcv_df['Volume'].values,
             'cash' : get_cash_including_position(cerebro_run),
             'percent_change' : get_percent_cash_change(cerebro_run),
             'trades' : get_trades_from_cerebro_run(cerebro_run),
             'buy' : get_buy_sell_from_cerebro_run(cerebro_run, trade_type='buy'),
             'sell' : get_buy_sell_from_cerebro_run(cerebro_run, trade_type='sell')
            }
    return pd.DataFrame(data=data, index=index) 

def get_candlestick_plot(data):
    #returns a candlestick plot from a dataframe with Open, High, Low, and Close columns
    return go.Candlestick(x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'])

if __name__ == '__main__':
    myset = backtrader_set(['ETH/BTC'], MaCrossStrategy, bt.sizers.PercentSizer, 10, '1/1/18', '1/1/20')
    myset.run()