from collections import defaultdict
from typing import OrderedDict, Type
from dataclasses import dataclass,field
import backtrader as bt
from datetime import datetime
import plotly.graph_objects as go
from backtrader.utils import num2date
import pandas as pd
import numpy as np

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
    fig = go.Figure(layout = {'title': indicator_plot_info.name})
    for line_plot_info in indicator_plot_info.line_list:
        plot = get_plot_from_line_plot_info(df, line_plot_info)
        fig.add_trace(plot)
    return fig

def get_plot_from_line_plot_info(df: pd.DataFrame, line_plot_info: pi.LinePlotInfo):
    """creates a plot for a single line of an indicator"""
    return go.Scatter(x=df.index, y=df[line_plot_info.line_name], mode=line_plot_info.mode, marker=line_plot_info.markers)


if __name__ == '__main__':
    main()
    
