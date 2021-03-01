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
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import numpy as np
import plotly.express as px


class backtrader_set():

    def __init__(self):
        self.cerebro_run_data = None #placeholder
        df = pd.DataFrame({
            "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
            "Amount": [4, 1, 2, 2, 4, 5],
            "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
            })
        
        self.fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

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
    
def get_trades_from_cerebro_run(cerebro_run, trade_type='long'):
    #get trades. Long is 'long' and shorts is 'short'. This is unconfirmed. Need to verify
    data = None
    for strat in cerebro_run[0].stats:
        if isinstance(strat, bt.observers.trades.DataTrades):
            trades = np.frombuffer(strat.lines[0].array)
            if trade_type == 'long':
                return trades[:int(len(trades) / 2)]
            else:
                return trades[int(len(trades) / 2):]
    return data
        
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