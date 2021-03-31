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
    _mindatas = 1

    lines = ('slope',)

    #plotinfo = dict(plotymargin=0.05, plotyhlines=[-1.0, 1.0])
    
    def next(self):
        if not isnan(self.data[1]):
            self.lines.slope[0] = self.data[0] - self.data[1]
            print("self.data[0] - self.data[1] =",self.data[0] - self.data[1])