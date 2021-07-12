import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

import pandas as pd
import rba_tools.retriver.get_crypto_data as gcd
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat

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
    #cerebro.addstrategy(MaCrossStrategy)
    cerebro.addstrategy(rbsstrat.TestStrategy, period=7)

    # Get a pandas dataframe
    binance = gcd.getBinanceExchange()
    dataframe = gcd.get_DataFrame(['ETH/BTC'], binance, '1/1/19', '12/31/19')

    if print_df:
        print('--------------------------------------------------')
        print(dataframe)
        print('--------------------------------------------------')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               nocase=True,
                               )

    cerebro.adddata(data)

    #cerebro.addanalyzer(CashMarket, _name='cash_market')

    # Run over everything
    strats = cerebro.run()

    # Plot the result
    if plot:
        myp = cerebro.plot(numfigs=1, style='bar')
        print(myp)


if __name__ == '__main__':
    runstrat()
