from typing import Optional
import backtrader as bt
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import rba_tools.constants as constants

from rba_tools.retriever.get_crypto_data import DataPuller
import rba_tools.backtest.backtrader_extensions.strategies as rbsstrat
from rba_tools.backtest.backtrader_extensions.plotting.data_plot_info_container import DataPlotInfoContainer
from rba_tools.backtest.backtrader_extensions.plotting.data_plot_info import DataPlotInfo
from rba_tools.backtest.backtrader_extensions.plotting.indicator_plot_info import IndicatorPlotInfo
from rba_tools.backtest.backtrader_extensions.plotting.line_plot_info import LinePlotInfo



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


#Indicator Plotting:

def plot_indicator(df: pd.DataFrame, indicator_plot_info: IndicatorPlotInfo, start: Optional[datetime] = None, end: Optional[datetime] = None):
    """plots an indicator given the associated DataFrame and plot info"""
    start = start if start is not None else df.index[0]
    end = end if end is not None else df.index[-1]
    fig = go.Figure(layout = {'title': indicator_plot_info.name,
                               'showlegend': True,
                               'xaxis' : {'rangeslider': {'visible': False},
                                          'autorange': False,
                                          'range' : [start, end]}
                               #could implement y-axis scaling
                                          })
    plot_list = get_indicator_plot_list(df, indicator_plot_info)
    for plot in plot_list:
        fig.add_trace(plot)
    return fig

def get_indicator_plot_list(df: pd.DataFrame, indicator_plot_info: IndicatorPlotInfo):
    """get list of indicator plots"""
    plot_list = []
    for line_plot_info in indicator_plot_info.line_list:
        plot_list.append(get_plot_from_line_plot_info(df, line_plot_info))
    return plot_list

def truncate_str_to_max_chars(string: str):
    if len(string) <= constants.PLOT_LEGEND_MAX_CHARACTERS:
        return string
    return string[0:18] + '..'



#LinePlotInfo Plotting:

def get_plot_from_line_plot_info(df: pd.DataFrame, line_plot_info: LinePlotInfo):
    """creates a plot for a single line of an indicator"""
    name = truncate_str_to_max_chars(line_plot_info.line_name)
    return go.Scatter(x=df.index,
                      y=df[line_plot_info.line_name],
                      mode=line_plot_info.mode,
                      marker=line_plot_info.markers,
                      name=name)



#DataPlotInfo Plotting

def get_candlestick_plot_title_from_dpi(dpi: DataPlotInfo):
    return dpi.symbol + ' (' + dpi.timeframe + ')'

def get_candlestick_plot_from_dpi(dpi: DataPlotInfo, start: Optional[datetime] = None, end: Optional[datetime] = None):
    """Creates a candle stick plot from a DataPlotInfo"""
    title = get_candlestick_plot_title_from_dpi(dpi)
    start = start if start is not None else dpi.df.index[0]
    end = end if end is not None else dpi.df.index[-1]
    range_min = dpi.df.loc[start:end, 'Low'].values.min()
    range_max = dpi.df.loc[start:end, 'High'].values.max()
    fig = go.Figure(layout = {'title': title,
                               'showlegend': True,
                               'plot_bgcolor': constants.COLORS['background'],
                               'paper_bgcolor': constants.COLORS['background'],
                               'xaxis' : {'rangeslider': {'visible': False},
                                          'autorange': False,
                                          'range' : [start, end]},
                               'yaxis': {'range' : [range_min, range_max]}
                             })
    fig.add_trace(get_candlestick_plot_from_df(dpi.df, dpi.symbol))

    for plt in get_overlay_plot_list_from_dpi(dpi):
        fig.add_trace(plt)
    return fig


def get_overlay_plot_list_from_indicator(df: pd.DataFrame, indicator: IndicatorPlotInfo):
    """get list of plots marked overlay from IndicatorPlotInfo"""
    plot_list = []
    for line_info in indicator.line_list:
        if line_info.overlay:
            plot_list.append(get_plot_from_line_plot_info(df, line_info))
    return plot_list


def get_overlay_plot_list_from_dpi(dpi: DataPlotInfo):
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


#DataPlotInfoContainerPlotting

def get_data_plot_info_container_plot_list(dpic: DataPlotInfoContainer, start: Optional[datetime] = None, end: Optional[datetime] = None):
    """gets list of plots for a DataPlotInfoContainer"""
    plot_list = []
    
    for dpi in dpic.data_and_plots_list:
        dpi_start = start if start is not None else dpi.df.index[0]
        dpi_end = end if end is not None else dpi.df.index[-1]
        plot_list.append(get_candlestick_plot_from_dpi(dpi, dpi_start, dpi_end))
        for ind in dpi.indicator_list:
            if ind.overlay or not indicator_has_values(dpi.df, ind):
                continue
            plot_list.append(plot_indicator(dpi.df, ind, dpi_start, dpi_end))

    return plot_list

def indicator_has_values(df: pd.DataFrame, indicator_plot_info: IndicatorPlotInfo) -> bool:
    """returns False if every value of every line of an indicator is nan. Otherwise True"""
    all_nan = True
    for line in indicator_plot_info.line_list:
        all_nan = not df[line.line_name].isnull().all()
        if all_nan:
            break
    return all_nan



if __name__ == '__main__':
    main()