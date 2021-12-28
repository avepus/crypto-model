

import backtrader as bt
import backtrader.feeds as btfeeds

import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat



def runstrat(plot=True): #Need stop loss, need to ensure proper behavior with sell target and with closing. why are orders rejected?

    # Create a cerebro entity
    cerebro = bt.Cerebro(runonce=False)

    # Add a strategy
    #cerebro.addstrategy(rbsstrat.TestStrategy, period=7)
    cerebro.addstrategy(rbsstrat.TestStrategy)

    #get a datapuller
    puller = gcd.DataPuller.kraken_puller()

    #symbol and date range
    symbol = 'ETH/USD'
    from_date = '1/1/20'
    to_date = '12/31/20'

    # Get a pandas dataframe
    dataframe = puller.fetch_df(symbol, 'h', from_date, to_date)

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               nocase=True,
                               )
    cerebro.adddata(data)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1440)

    # Run over everything
    cerebro.run()

    # Plot the result
    if plot:
        myp = cerebro.plot(numfigs=1, style='bar')
        print(myp)


if __name__ == '__main__':
    runstrat()
