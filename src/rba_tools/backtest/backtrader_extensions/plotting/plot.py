from collections import defaultdict
from typing import OrderedDict, Type
from dataclasses import dataclass,field
import backtrader as bt
from datetime import datetime
import plotly.graph_objects as go
from backtrader.utils import num2date
import pandas as pd
import numpy as np
import rba_tools.constants as constants

from rba_tools.retriever.get_crypto_data import DataPuller
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat
import rba_tools.backtest.backtrader_extensions.plotting.plotinfo as pi



def main():
    cerebro = bt.Cerebro(runonce=False)

    #cerebro.addstrategy(rbsstrat.MaCrossStrategy)
    cerebro.addstrategy(rbsstrat.TestStrategy, period=7)
    #cerebro.addstrategy(rbsstrat.ConsecutiveBarsTest)
    #cerebro.addstrategy(rbsstrat.StopLimitEntryStrategy)
    puller = DataPuller.kraken_puller()

    #symbol and date range
    symbol = 'ETH/USD'
    from_date = '1/1/20'
    to_date = '6/30/20'

    dataframe = puller.fetch_df(symbol, 'h', from_date, to_date)

    # Pass it to the backtrader datafeed and add it to the cerebro
    data = bt.feeds.PandasData(dataname=dataframe,
                                nocase=True,
                                )
    #cerebro.adddata(data)
    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=240)

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1440)

    # Run over everything
    back = cerebro.run()
    #myp = cerebro.plot(numfigs=1, style='bar')

    #DataAndPlotInfoContainer(back[0])


def plot_indicator(df: pd.DataFrame, indicator_plot_info: pi.IndicatorPlotInfo):
    """plots an indicator given the associated DataFrame and plot info"""
    fig = go.Figure(layout = {'title': indicator_plot_info.name,
                               'showlegend': True})
    plot_list = get_indicator_plot_list(df, indicator_plot_info)
    for plot in plot_list:
        fig.add_trace(plot)
    return fig

def get_indicator_plot_list(df: pd.DataFrame, indicator_plot_info: pi.IndicatorPlotInfo):
    """get list of indicator plots"""
    plot_list = []
    for line_plot_info in indicator_plot_info.line_list:
        plot_list.append(get_plot_from_line_plot_info(df, line_plot_info))
    return plot_list

def truncate_str_to_max_chars(string: str):
    if len(string) <= constants.PLOT_LEGEND_MAX_CHARACTERS:
        return string
    return string[0:18] + '..'


def get_plot_from_line_plot_info(df: pd.DataFrame, line_plot_info: pi.LinePlotInfo):
    """creates a plot for a single line of an indicator"""
    name = truncate_str_to_max_chars(line_plot_info.line_name)
    return go.Scatter(x=df.index,
                      y=df[line_plot_info.line_name],
                      mode=line_plot_info.mode,
                      marker=line_plot_info.markers,
                      name=name)



def get_candlestick_plot_from_dpi(dpi: pi.DataPlotInfo):
    """Creates a candle stick plot from a DataPlotInfo"""
    title = dpi.symbol + ' (' + dpi.timeframe + ')'
    fig = go.Figure(layout = {'title': title,
                               'showlegend': True,
                               'xaxis' : {'rangeslider': {'visible': False},
                                          'autorange': True}
                             })
    fig.add_trace(get_candlestick_plot_from_df(dpi.df, dpi.symbol))
    for indicator in dpi.indicator_list:
        
        for line_info in indicator.line_list:
            if not line_info.plotinfo.get('_overlay'):
                continue
    plot_list = get_overlay_plot_list_from_dpi(dpi)
    for plt in plot_list:
        fig.add_trace(plt)
    return fig

def get_overlay_plot_list_from_indicator(df: pd.DataFrame, indicator: pi.IndicatorPlotInfo):
    """get list of plots marked overlay from IndicatorPlotInfo"""
    plot_list = []
    for line_info in indicator.line_list:
        if line_info.overlay:
            plot_list.append(get_plot_from_line_plot_info(df, line_info))
    return plot_list

def get_overlay_plot_list_from_dpi(dpi: pi.DataPlotInfo):
    """get list of plots marked overlay from DataPlotInfo"""
    plot_list = []
    for ind in dpi.indicator_list:
        plot_list = plot_list + get_overlay_plot_list_from_indicator(dpi.df, ind)
    return plot_list


def get_candlestick_plot_from_df(df: pd.DataFrame, symbol: str):
    #returns a candlestick plot from a dataframe with Open, High, Low, and Close columns
    return go.Candlestick(x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol)


if __name__ == '__main__':
    main()