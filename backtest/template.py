import argparse

import backtrader as bt
import backtrader.feeds as btfeeds

import pandas as pd
import rba_tools.retriver.get_crypto_data as gcd
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat



def runstrat(plot=True): #Need stop loss, need to ensure proper behavior with sell target and with closing. why are orders rejected?

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(rbsstrat.TestStrategy, period=7)

    # Get a pandas dataframe
    binance = gcd.getBinanceExchange()
    dataframe = gcd.get_DataFrame(['ETH/BTC'], binance, '1/1/19', '12/31/19')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               nocase=True,
                               )
    cerebro.adddata(data)

    replay_df = gcd.get_DataFrame(['ETH/BTC'], binance, '1/1/19', '12/31/19', timeframe='1h')

    replay_data = bt.feeds.PandasData(dataname=replay_df,
                               nocase=True,
                               )

    cerebro.replaydata(replay_data, timeframe=bt.TimeFrame.Minutes, compression=60)

    # Run over everything
    strats = cerebro.run()

    # Plot the result
    if plot:
        myp = cerebro.plot(numfigs=1, style='bar')
        print(myp)


if __name__ == '__main__':
    runstrat()
