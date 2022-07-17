# -*- coding: utf-8 -*-
"""Custom backtrader indicators

Created on Tues Mar 30 2021

@author: Avery

"""

import backtrader as bt
from numpy import isnan


class Slope(bt.Indicator):
    '''
    This indicator gives the slope of the input line.
    '''

    lines = ('slope',)

    def __init__(self):
        self.lines.slope = self.data - self.data(-1)

class LowHighRatio(bt.Indicator):
    """
    This indicator calculates the lowest low divided by the highest high over the lookback period
    Theory being that the closer to 1 the more the consolidated the market is
    """

    params = (('period',5),('threshold',92.5),)

    lines = ('low_high_ratio','threshold')

    plotlines = dict(threshold=dict(color='black'),
                      low_high_ratio=dict(_fill_gt=('threshold', 'green')))

    plotinfo = dict(plotyticks=[50, 100])
    def __init__(self):
        self.threshold = bt.Max(self.p.threshold, self.p.threshold)
        self.lines.low_high_ratio = bt.indicators.Lowest(self.data.low, period=self.p.period) / bt.indicators.Highest(self.data.high, period=self.p.period) * 100


class ConsecutiveBars(bt.Indicator):
    """
    This indicator counts the number of consecutive bars green/red bars
    positive number implies consecutive green bars and negative implies red
    """

    lines = ('consecutive_bars',)

    def next(self):
        closed_above_open = self.data.close[0] > self.data.open[0] #green bar
        if closed_above_open:
            if self.lines.consecutive_bars[-1] < 0 or isnan(self.lines.consecutive_bars[-1]):
                self.lines.consecutive_bars[0] = 1
            else:
                self.lines.consecutive_bars[0] = self.lines.consecutive_bars[-1] + 1
            return

        closed_below_open = self.data.close[0] < self.data.open[0] #red bar
        if closed_below_open:
            if self.lines.consecutive_bars[-1] > 0 or isnan(self.lines.consecutive_bars[-1]):
                self.lines.consecutive_bars[0] = -1
            else:
                self.lines.consecutive_bars[0] = self.lines.consecutive_bars[-1] - 1
            return
        
        #this would be case when close = open
        self.lines.consecutive_bars[0] = self.lines.consecutive_bars[-1]

class InTrend(bt.Indicator):
    """
    Build this with some combination of consecutive bars and if it retraces past a certain point the trend is done
    params:
    minimum_bars - at least this many consecutive bars are needed to call it a trend
    maximum_bars - a trend can only be this many bars long (a new trend within a trend will reset this)
    minimum_move_percent - minimum amount between open of starting trend bar and maximum to call it a trend
    trend_retrace_percent - the max a trend can retrace. If it retraces past this the trend is done
    lines:
    consecutive_bars - see ConsecutiveBars
    in_trend - 0 means not in trend. 1 means in positive trend. Maybe someday -1 will mean in negative trend
    trend_started_ago - number of bars ago that the trend started
    trend_high - high of the trend
    """

    params = (('minimum_bars',2),('maximum_bars',20),('minimum_move_percent',20),('trend_retrace_percent',85),)

    lines = ('consec_bars', 'trend_started_ago', 'trend_high', 'trend_retrace', 'trend_open')

    plotlines = dict(consec_bars=dict(color="black"),
                     trend_started_ago=dict(color="red", _method="scatter"),
                     trend_high=dict(color="blue"),
                     trend_retrace=dict(_plotskip=True),
                     trend_open=dict(_plotskip=True))
    def __init__(self):
        self.lines.consec_bars = ConsecutiveBars(self.data)

    def next(self):
        consecutive_bar_start = int(-1 * abs(self.lines.consec_bars[-1]))

        if consecutive_bar_start > len(self.data.open) - 1:
            return
        
        if self.lines.consec_bars[0] == -1:
            #we just turned down, need to check if this is a new trend
            over_min_bars = self.lines.consec_bars[-1] > self.p.minimum_bars

            high = max(self.data.high[-1],self.data.high[0])
            percent_to_high = (high - self.data.open[consecutive_bar_start]) / self.data.open[consecutive_bar_start] * 100
            over_min_percent = percent_to_high > self.p.minimum_move_percent

            if over_min_bars and over_min_percent: #new trend
                self.lines.trend_high[0] = high
                self.lines.trend_started_ago[0] = consecutive_bar_start
                self.lines.trend_open[0] = self.data.open[consecutive_bar_start]
                return
        

        if isnan(self.lines.trend_started_ago[-1]):
            return

        #last bar we were in a trend, check if we're still in a trend
        trend_start_bars_back = int(self.lines.trend_started_ago[-1]) - 1

        
        trend_exceeds_max_bars = abs(trend_start_bars_back) > self.p.maximum_bars
        if trend_exceeds_max_bars:
            return

        temp_high = self.lines.trend_high[-1]
        current_retrace_percent = (1 - (self.data.low[0] - self.data.open[trend_start_bars_back]) / (temp_high - self.data.open[trend_start_bars_back])) * 100
        self.lines.trend_retrace[0] = current_retrace_percent
        trend_retraced_too_far = current_retrace_percent > self.p.trend_retrace_percent
        if trend_retraced_too_far:
            return
        
        #if we didn't hit any exceptions, the trend continues
        self.lines.trend_started_ago[0] = trend_start_bars_back
        self.lines.trend_open[0] = self.data.open[trend_start_bars_back]

        #check if new high was made
        if self.lines.trend_high[-1] > self.data.high[0]:
            self.lines.trend_high[0] = self.lines.trend_high[-1]
        else:
            self.lines.trend_high[0] = self.data.high[0]

class Retrace_Percent(bt.Indicator):
    #Separated out from TrendInfo for graphing, likely not needed long-term
    lines = ('trend_retrace',)

    plotinfo = dict(plotyticks=[0, 100])
    plotlines = dict(trend_retrace=dict(_plotskip=False, _method="scatter"))

    def __init__(self):
        self.lines.trend_retrace = InTrend(self.data).trend_retrace

class Trend_High(bt.Indicator):
    #Separated out from TrendInfo for graphing, likely not needed long-term
    lines = ('trend_high',)
    plotinfo = dict(subplot=False)
    plotlines = dict(trend_high=dict(_plotskip=False, _method="scatter"))

    def __init__(self):
        self.lines.trend_high = InTrend(self.data).trend_high

class Trend_Open(bt.Indicator):
    #Separated out from TrendInfo for graphing, likely not needed long-term
    lines = ('trend_open',)
    plotinfo = dict(subplot=False)
    plotlines = dict(trend_open=dict(_plotskip=False, _method="scatter", color="green"))

    def __init__(self):
        self.lines.trend_open = InTrend(self.data).trend_open

class TrendInfo(bt.Indicator):
    """
    This indicator tracks trendinfo
    trend_start = open of the first green bar of the trend
    trend_max = high of the trend
    trend_percentage = percent change from trend start
    """

    lines = ('consecutive_bars','trend_start','trend_percentage')

    def __init__(self):
        self.lines.consecutive_bars = ConsecutiveBars(self.data)

    def next(self):
        if self.lines.consecutive_bars[0] > 3:
            ago = int(-1 * self.lines.consecutive_bars[0])
            self.lines.trend_start[0] = self.data.open[ago]
            self.lines.trend_percentage[0] = self.data.close[0] / self.lines.trend_start[0] * 100

class CashMarket(bt.analyzers.Analyzer):
    """
    Analyzer returning cash and market values for use in QuantStats
    """

    def start(self):
        super(CashMarket, self).start()

    def create_analysis(self):
        self.rets = {}
        self.vals = 0.0

    def notify_cashvalue(self, cash, value):
        self.vals = (cash, value)
        self.rets[self.strategy.datetime.datetime()] = self.vals

    def get_analysis(self):
        return self.rets