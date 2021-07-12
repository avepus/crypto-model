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

    params = (
        ('period', 5),
        ('threshold',92.5),
        )

    def __init__(self):
        ma = bt.ind.SMA(period = 10)
        #self.maslope = rbsind.Slope(ma)
        #self.lowhigh = rbsind.LowHighRatio(self.data, period=self.p.period, threshold=self.p.threshold)
        #self.con_bars = rbsind.TrendInfo(self.data)
        self.in_trend = rbsind.InTrend(self.data)
        self.retrace_percent = rbsind.Retrace_Percent(self.data)
        self.trend_high = rbsind.Trend_High(self.data)
        self.trend_open = rbsind.Trend_Open(self.data)

    def next(self):
        #print("con_bars =",self.con_bars[0])
        #print("consecutive_bars =",self.con_bars.consecutive_bars[0])
        #print("trend_start =",self.con_bars.trend_start[0])
        #print("trend_percentage =",self.con_bars.trend_percentage[0])
        print("consec_bars =",self.in_trend.consec_bars[0])
        print("trend_started_ago =",self.in_trend.trend_started_ago[0])
        print("trend_high =",self.in_trend.trend_high[0])
        print("trend_retrace =",self.in_trend.trend_retrace[0])
        print("trend_open =",self.in_trend.trend_open[0])
        print("date =",self.datetime.datetime())
        #if len(self.maslope) < 2:
        #    return
        #if self.lines.consecutive_bars[0] == -1 and self.lines.consecutive_bars[-1] > 6:
        #    self.buy()
        #elif self.lines.consecutive_bars[0] < -2:
        #    self.sell()