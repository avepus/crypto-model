# -*- coding: utf-8 -*-
"""Default run info mainly for testing/validation

Created 7/17/22

@author: Avery

"""
from typing import Optional
import backtrader as bt
from rba_tools import DataPlotInfoContainer
from rba_tools.backtest.backtrader_extensions.plotting.data_plot_info_container import pickle_dpic
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat
from rba_tools.retriever.get_crypto_data import DataPuller


def default_data():
    """returns the default data for a cerebro run"""
    puller = DataPuller.kraken_puller()
    symbol = 'ETH/USD'
    from_date = '1/1/20'
    to_date = '6/30/20'
    return puller.fetch_df(symbol, 'h', from_date, to_date)

def add_default_strategy(cerebro: bt.Cerebro):
    """returns the default data for a cerebro run"""
    #cerebro.addstrategy(MaCrossStrategy)
    cerebro.addstrategy(rbsstrat.TestStrategy, period=7)
    #cerebro.addstrategy(rbsstrat.TestMultStrategy)
    #cerebro.addstrategy(rbsstrat.ConsecutiveBarsTest)
    #cerebro.addstrategy(rbsstrat.StopLimitEntryStrategy)
    #cerebro.addstrategy(rbsstrat.TestMultStrategy2)

def run_multiple_timeframe(strategy: Optional[bt.Strategy] = None, save: bool = False):
    cerebro = bt.Cerebro(runonce=False)

    # Add a strategy
    if strategy:
        cerebro.addstrategy(strategy)
    else:
        add_default_strategy(cerebro)

    # Get a pandas dataframe
    dataframe = default_data()

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                                nocase=True,
                                )
    #cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=240)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1440)

    dpic = DataPlotInfoContainer(cerebro.run()[0])

    if save:
        pickle_dpic(dpic)
    return dpic


def run_single_timeframe(strategy: Optional[bt.Strategy] = None, save: bool = False):
    cerebro = bt.Cerebro(runonce=False)

    # Add a strategy
    if strategy:
        cerebro.addstrategy(strategy)
    else:
        add_default_strategy(cerebro)

    # Get a pandas dataframe
    dataframe = default_data()

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                                nocase=True,
                                )
    #cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1440)

    dpic = DataPlotInfoContainer(cerebro.run()[0])

    if save:
        pickle_dpic(dpic)
    return dpic
