from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

import pandas
import get_crypto_data as gcd

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


def runstrat(print_df=False, plot=True):

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(MaCrossStrategy)

    # Get a pandas dataframe
    binance = gcd.getBinanceExchange()
    dataframe = gcd.get_DataFrame(['ETH/BTC'], binance, '1/1/18', '12/31/19')

    if print_df:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               nocase=True,
                               )

    cerebro.adddata(data)

    # Run over everything
    strats = cerebro.run()

    # Plot the result
    if plot:
        cerebro.plot(style='bar')


if __name__ == '__main__':
    runstrat()
