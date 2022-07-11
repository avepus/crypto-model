from typing import List,Optional
from dataclasses import dataclass
from rba_tools.backtest.backtrader_extensions.plotting.line_plot_info import LinePlotInfo







@dataclass
class IndicatorPlotInfo():
    """holds indicator level plot info which consists of the
    name of the indicator and a list of LinePlotInfo objects.
    This is the "figure" level of the plotting"""
    name: str
    line_list: List[LinePlotInfo]
    overlay: Optional[bool] = False
