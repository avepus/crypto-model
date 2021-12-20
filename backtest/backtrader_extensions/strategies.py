# -*- coding: utf-8 -*-
"""Custom backtrader strategies

Created on Tues Mar 30 2021

@author: Avery

"""

import backtrader as bt
import rba_tools.backtest.backtrader_extensions.indicators as rbsind
from numpy import isnan

class StopLimitEntryStrategy(bt.Strategy):
    pass

class TrailingStopStrategy(bt.Strategy):
    pass

class TestStrategy(bt.Strategy):

    params = (
        ('period', 5),
        ('threshold',92.5),
        ('debug',True),
        ('max_drawdown_pct',10)
        )

    def __init__(self):
        ma = bt.ind.SMA(period = 10)
        #self.maslope = rbsind.Slope(ma)
        #self.lowhigh = rbsind.LowHighRatio(self.data, period=self.p.period, threshold=self.p.threshold)
        #self.con_bars = rbsind.TrendInfo(self.data)
        self.in_trend = inTrend = rbsind.InTrend(self.data1)
        self.retrace_percent = rbsind.Retrace_Percent(self.data1)
        self.trend_high = rbsind.Trend_High(self.data1)
        self.trend_open = rbsind.Trend_Open(self.data1)
        if self.params.debug:
            open('run_log.txt', 'w').close() #clear out file at during init if we're writing to file

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        with open('run_log.txt', 'a') as myfile:
            myfile.write('%s, %s' % (dt.isoformat(), txt))
            myfile.write('\n')

    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def debug_print(self):
        """
        Prints debug data to file for investigating details
        """
        log_string = ""
        #print("con_bars =",self.con_bars[0])
        #print("consecutive_bars =",self.con_bars.consecutive_bars[0])
        #print("trend_start =",self.con_bars.trend_start[0])
        #print("trend_percentage =",self.con_bars.trend_percentage[0])
        log_string = log_string + "\n" + "consec_bars=" + str(self.in_trend.consec_bars[0])
        log_string = log_string + "\n" + "trend_started_ago=" + str(self.in_trend.trend_started_ago[0])
        log_string = log_string + "\n" + "trend_high=" + str(self.in_trend.trend_high[0])
        log_string = log_string + "\n" + "trend_retrace=" + str(self.in_trend.trend_retrace[0])
        log_string = log_string + "\n" + "trend_open=" + str(self.in_trend.trend_open[0])
        if self.position:
            log_string = log_string + "\n" + "position=" + str(self.position)

        self.log(log_string)

    def next(self):
        if self.params.debug:
            self.debug_print()
        # Check if we are in the market
        if not self.position:
            if self.in_trend.trend_retrace.s1() < 50:
                o1 = self.buy()
                #self.log('o1=' + str(o1))
                o2 = self.sell(exectype=bt.Order.Limit, price=self.in_trend.trend_high[0])
                #self.log('o2=' + str(o2))
                stopLoss = self.data.close[0] * (1 - (self.p.max_drawdown_pct / 100))
                o3 = self.sell(price=stopLoss,exectype=bt.Order.Stop, oco=o2)
                #self.log('o3=' + str(o3))
        else:
            #if there is no trend then close
            if isnan(self.in_trend.trend_retrace.s1()):
                self.close()