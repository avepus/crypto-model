from typing import List
from dataclasses import dataclass
from pandas import DataFrame
from rba_tools.backtest.backtrader_extensions.plotting.indicator_plot_info import IndicatorPlotInfo


@dataclass
class DataPlotInfo:
    """Holds the actual data from the cerebro run in a dataframe
    as well as the list of the IndicatorPlotInfo objects from that run
    This is the "timeframe" level of reporting"""
    df: DataFrame
    symbol: str
    timeframe: str
    indicator_list: List[IndicatorPlotInfo]
    