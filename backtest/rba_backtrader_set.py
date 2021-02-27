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
    
    def get_trades_from_cerebro_run(self):
        #gets the trade array from the return of cerebro.run()
        data = None
        for strat in self.cerebro_run_data[0].stats:
            print(strat)
            if isinstance(strat, bt.observers.trades.DataTrades):
                for line in strat.lines:
                    npary = np.frombuffer(line.array)
                    if len(npary[~np.isnan(npary)]) > 0:
                        data = npary
        return data
        

    