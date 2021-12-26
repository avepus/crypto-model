

import backtrader as bt
import backtrader.feeds as btfeeds

import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat



def runstrat(plot=True): #Need stop loss, need to ensure proper behavior with sell target and with closing. why are orders rejected?

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(rbsstrat.TestStrategy, period=7)

    #get a datapuller
    puller = gcd.DataPuller.use_defaults()

    # Get a pandas dataframe
    dataframe = puller.fetch_df('ETH/BTC', 'd', '1/1/19', '12/31/19')

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                               nocase=True,
                               )
    cerebro.adddata(data)

    # replay_df = puller.fetch_df('ETH/BTC', 'h', '1/1/19', '12/31/19')

    # replay_data = bt.feeds.PandasData(dataname=replay_df,
    #                            nocase=True,
    #                            )

    # cerebro.replaydata(replay_data, timeframe=bt.TimeFrame.Minutes, compression=60)

    # Run over everything
    cerebro.run()

    # Plot the result
    if plot:
        myp = cerebro.plot(numfigs=1, style='bar')
        print(myp)


if __name__ == '__main__':
    runstrat()
