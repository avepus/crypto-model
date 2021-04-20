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

class LowHighRatio(bt.Indicator): #need to make this take the highs and the lows as input
    """
    This indicator calculates the lowest low divided by the highest high over the lookback period
    Theory being that the closer to 1 the more the consolidated the market is
    """

    params = (('period',5),('threshold',0.925),)

    lines = ('low_high_ratio','threshold')

    plotlines = dict(threshold=dict(color='black'),
                      low_high_ratio=dict(_fill_gt=('threshold', 'green')))

    def __init__(self):
        self.threshold = bt.Max(self.p.threshold, self.p.threshold)
        self.lines.low_high_ratio = bt.indicators.Lowest(self.data.low, period=self.p.period) / bt.indicators.Highest(self.data.high, period=self.p.period)