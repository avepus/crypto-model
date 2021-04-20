# -*- coding: utf-8 -*-
"""Custom backtrader strategies

Created on Tues Mar 30 2021

@author: Avery

"""

import backtrader as bt
import rba_tools.backtest.backtrader_extensions.indicators as rbsind

class StopLimitEntryStrategy(bt.Strategy):
    pass

class TrailingStopStrategy(bt.Strategy):
    pass

class TestStrategy(bt.Strategy):

    def __init__(self):
        ma = bt.ind.SMA(period = 10)
        self.maslope = rbsind.Slope(ma)
        self.lowhigh = rbsind.LowHighRatio(self.data, period=7)

    def next(self):
        if len(self.maslope) < 2:
            return
        if self.maslope[0] > 0 and self.maslope[-1] < 0:
            self.buy()
        elif self.maslope[0] < 0 and self.maslope[-1] > 0:
            self.close()