from typing import Union, Optional, List, Type
import pickle
import os
from fnmatch import fnmatch
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from pandas import DataFrame, Series
import backtrader as bt
from datetime import datetime
from rba_tools.constants import get_pickle_root
from rba_tools.backtest.backtrader_extensions.plotting.data_plot_info import DataPlotInfo
from rba_tools.backtest.backtrader_extensions.plotting.indicator_plot_info import IndicatorPlotInfo
from rba_tools.backtest.backtrader_extensions.plotting.line_plot_info import LinePlotInfo


GLOBAL_TOP = 'global_top'
UPPER = 'upper'
LOWER = 'lower'
OVERLAY = 'overlay'


@dataclass
class DataPlotInfoContainer():
    """Class holds a list of DataPlotInfo objects
    This is the "Strategy" level of reporting

    Note: this isn't really ok but it takes a strategy as an
        input but only ends up saving that strategy name
        after it uses the strategy to populate everything
    """

    strategy: Union[str, bt.Strategy]
    data_and_plots_list: Optional[List[DataPlotInfo]] = None

    def __post_init__(self):
        if isinstance(self.strategy, bt.Strategy):
            self.data_and_plots_list = get_dataframe_and_plot_dict(self.strategy)
            self.strategy = type(self.strategy).__name__


def pickle_dpic(dpic: DataPlotInfoContainer):
    """Creates pickle file for DataAndPlotInfoContainer"""
    def get_file_name(dpic: DataPlotInfoContainer) -> str:
        symbol = dpic.data_and_plots_list[0].symbol.replace('/','-')
        return datetime.now().strftime("%Y-%m-%d %H;%M;%S") + '_' + dpic.strategy + '_' + symbol + '.p'

    path = os.path.join(get_pickle_root(), get_file_name(dpic))

    with open(path, 'wb') as file:
        pickle.dump(dpic, file)

def unpickle_last_dpic() -> DataPlotInfoContainer:
    """Unpickles the most recently pickled DataAndPlotInfoContainer class"""
    pickle_dir_list = os.listdir(get_pickle_root())
    dpic_pickle_list = [f for f in pickle_dir_list if fnmatch(f, '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.p')]
    dpic_pickle_list.sort(reverse = True)
    path = os.path.join(get_pickle_root(), dpic_pickle_list[0])
    with open(path, 'rb') as file:
        return pickle.load(file)


def get_dataframe_and_plot_dict(strategy: Type[bt.Strategy]):
    """takes in a strategy and returns a list of DataAndPlots objects
    that hold the dataframe for a datafeed and the plots"""

    sorted_indicators = sort_indicators(strategy)

    return_list = []

    for index in range(len(strategy.datas)):
        indicator_list = []
        data = strategy.datas[index]
        df = get_ohlcv_data_from_data(data)
        symbol = get_symbol_from_bt_datafeed(data)
        timeframe = get_timeframe_name_from_bt_datafeed(data)

        add_figures_from_sorted_indicators(index, df, sorted_indicators, data, indicator_list)

        return_list.append(DataPlotInfo(df, symbol, timeframe, indicator_list))

    return return_list


def get_ohlcv_data_from_data(data):
    #get ohlcv dataframe from a backtrader feed
    start = 0
    end = len(data)
    datetime_float_ary = data.datetime.plot()
    datetime_list = [bt.utils.num2date(float_date) for float_date in datetime_float_ary]
    index = np.array(datetime_list)
    return DataFrame(data={
        'Open' : data.open.plotrange(start,end),
        'High' : data.high.plotrange(start,end),
        'Low' : data.low.plotrange(start,end),
        'Close' : data.close.plotrange(start,end),
        'Volume' : data.volume.plotrange(start,end)
        },
        index=index)


def add_figures_from_sorted_indicators(index: int, df: DataFrame, sorted_indicators: dict, data, indicator_list: list):
    """Adds all indicator lines to the passed in dataframe and the go_figure_list

    Args:
        index (int): current index of strategy datas being looped over
        df (pd.DataFrame): DataFrame which data will be added to
        sorted_indicators (dict): dictionary of sorted indicators
        go_figure_list (list): list of figures that new figures will be appended to
        data (_type_): backtrader data feed currently being run over
    """
    if index == 0:
        #add global top indicators only to the first data
        for indicator in sorted_indicators[GLOBAL_TOP]:
            populate_df_and_graphs_from_sorted_indicators(df, indicator, sorted_indicators, indicator_list)
    
    for indicator in sorted_indicators[UPPER][data]:
        populate_df_and_graphs_from_sorted_indicators(df, indicator, sorted_indicators, indicator_list)

    for indicator in sorted_indicators[OVERLAY][data]:
        populate_df_and_graphs_from_sorted_indicators(df, indicator, sorted_indicators, indicator_list, overlay=True)

    for indicator in sorted_indicators[LOWER][data]:
        populate_df_and_graphs_from_sorted_indicators(df, indicator, sorted_indicators, indicator_list)


def populate_df_and_graphs_from_sorted_indicators(df: DataFrame, indicator: bt.indicator, sorted_indicators: dict, indicator_list: list, overlay=False):
    """adds mapped top and bottom indicators and the passed in indicator to dataframe"""
    for inner_indicator in sorted_indicators[UPPER][indicator]:
        populate_df_and_graphs_from_sorted_indicators(df, inner_indicator, sorted_indicators, indicator_list)
    
    indicator_list.append(add_indicator_to_df_and_figure(df, indicator, overlay))

    for inner_indicator in sorted_indicators[LOWER][indicator]:
        populate_df_and_graphs_from_sorted_indicators(df, inner_indicator, sorted_indicators, indicator_list)


def add_indicator_to_df_and_figure(df: DataFrame, indicator: bt.indicator, overlay=False):
    """adds an indicator and all of it's lines to the dataframe and to a figure that
    is appended to the figure_list
    
    figure is used to optionally add all indicators to an existing figure rather than
    creating a new one"""
    lpi_list = []

    for line_index in range(indicator.size()):
        line = indicator.lines[line_index]
        name = get_indicator_line_name(indicator, line_index)
        indicator_vals = line.plotrange(0, len(line))
        df[name] = indicator_vals

        plotinfo = get_line_plot_info_from_indicator_line(indicator, line_index)
        mode = None if pandas_series_is_continuous(df[name]) else 'markers'
        lpi_list.append(LinePlotInfo(name, plotinfo, overlay, mode))

    return IndicatorPlotInfo(type(indicator).__name__, lpi_list, overlay)


def get_indicator_line_name(indicator: bt.indicator, index=0):
    """obtains the name of an individual line of a backtrader indicator"""
    alias = indicator.lines._getlinealias(index)
    return alias + ' (' + get_indicator_params_string(indicator) + ')'


def get_indicator_params_string(indicator: bt.indicator):
    """gets formatted paramaters from an indicator. They will be formatted as like so
    "param1name=value param2name=value ..."
    """
    params_str = ''
    param_dictionary = vars(indicator.p)
    if not param_dictionary:
        return params_str
    
    for key, value in param_dictionary.items():
        params_str += f' {key}={value}'
    
    return params_str.strip()


def get_line_plot_info_from_indicator_line(indicator:bt.indicator, line_index: int):
    """get the lineplotinfo from an indicator"""
    line_plot_info = getattr(indicator.plotlines, '_%d' % line_index, None)
    if line_plot_info:
        return line_plot_info._get_getkwargs()
    
    linealias = indicator.lines._getlinealias(line_index)
    line_plot_info = getattr(indicator.plotlines, linealias, None)
    if line_plot_info:
        return line_plot_info._getkwargs()

    #bt.AutoInfoClass() is what backtrader gets as the plot_info if we can't get it from the line
    return bt.AutoInfoClass()._getkwargs()


def get_symbol_from_bt_datafeed(data):
    """gets the symbol from a bt datafeed this only works
    for a pandas datafeed that has a 'Symbol' column"""
    symbol = None
    try:
        symbol = data._dataname['Symbol'].iat[0]
    except (KeyError, TypeError, AttributeError):
        pass
    return symbol

def pandas_series_is_continuous(series: Series) -> bool:
    """returns True if a series contains nan.
    Ignores the first nan values up to the first valid value and
    all nan values from the last valid value to the end"""
    series_first_valid_to_last_valid = series.loc[series.first_valid_index(): series.last_valid_index()]
    return len(series_first_valid_to_last_valid) == len(series_first_valid_to_last_valid.dropna())

def get_timeframe_name_from_bt_datafeed(data):
    """Gets timeframe name. Copied straight from backtrader.plot"""
    tfname = ''
    if hasattr(data, '_compression') and \
        hasattr(data, '_timeframe'):
        tfname = bt.TimeFrame.getname(data._timeframe, data._compression)
    return tfname

def sort_indicators(strategy: bt.Strategy):
    """Copy of bt.plot.Plot.sortdataindicators returned in a dictionary.
    I don't like this but figured it was best to keep exactly what backtrader
    does."""
    # These lists/dictionaries hold the subplots that go above each data
    plot_dictionary = {
        GLOBAL_TOP : list(),
        UPPER : defaultdict(list),
        LOWER : defaultdict(list),
        OVERLAY : defaultdict(list)
    }

    # Sort observers in the different lists/dictionaries
    for observer in strategy.getobservers():
        if not observer.plotinfo.plot or observer.plotinfo.plotskip:
            continue

        if observer.plotinfo.subplot:
            plot_dictionary[GLOBAL_TOP].append(observer)
        else:
            key = getattr(observer._clock, 'owner', observer._clock)
            plot_dictionary[OVERLAY][key].append(observer)

    # Sort indicators in the different lists/dictionaries
    for indicator in strategy.getindicators():
        if not hasattr(indicator, 'plotinfo'):
            # no plotting support - so far LineSingle derived classes
            continue

        if not indicator.plotinfo.plot or indicator.plotinfo.plotskip:
            continue

        indicator._plotinit()  # will be plotted ... call its init function

        # support LineSeriesStub which has "owner" to point to the data
        key = getattr(indicator._clock, 'owner', indicator._clock)
        if key is strategy:  # a LinesCoupler
            key = strategy.data

        if getattr(indicator.plotinfo, 'plotforce', False):
            if key not in strategy.datas:
                datas = strategy.datas
                while True:
                    if key not in strategy.datas:
                        key = key._clock
                    else:
                        break

        xpmaster = indicator.plotinfo.plotmaster
        if xpmaster is indicator:
            xpmaster = None
        if xpmaster is not None:
            key = xpmaster

        if indicator.plotinfo.subplot and xpmaster is None:
            if indicator.plotinfo.plotabove:
                plot_dictionary[UPPER][key].append(indicator)
            else:
                plot_dictionary[LOWER][key].append(indicator)
        else:
            plot_dictionary[OVERLAY][key].append(indicator)

    return plot_dictionary
