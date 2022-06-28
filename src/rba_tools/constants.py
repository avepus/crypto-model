from pandas import DataFrame, DatetimeIndex
from datetime import datetime,date
from os.path import join
from pathlib import Path
DATAFRAME_HEADERS = ['Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']
INDEX_HEADER = 'Timestamp'

def empty_ohlcv_df_generator():
    """Generates a new empty "open, high, low, close, volume" dataframe"""
    return DataFrame(columns=DATAFRAME_HEADERS, index=DatetimeIndex([], name=INDEX_HEADER))

def create_midnight_datetime_from_date(_date: date) -> datetime:
    return datetime.combine(_date, datetime.min.time())

def get_project_root() -> str:
    return str(Path(__file__).parent.parent)

def get_pickle_root() -> str:
    return join(get_project_root(), 'rba_tools', 'backtest', 'backtrader_extensions', 'data_plot_container_pickles')