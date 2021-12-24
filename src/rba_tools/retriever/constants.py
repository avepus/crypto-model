from pandas import DataFrame, DatetimeIndex
from datetime import datetime,date
DATAFRAME_HEADERS = ['Open', 'High', 'Low', 'Close', 'Volume', 'Symbol', 'Is_Final_Row']
INDEX_HEADER = 'Timestamp'

def empty_ohlcv_df_generator():
    """Generates a new empty "open, high, low, close, volume" dataframe"""
    return DataFrame(columns=DATAFRAME_HEADERS, index=DatetimeIndex([], name=INDEX_HEADER))

def create_midnight_datetime_from_date(_date: date) -> datetime:
    return datetime.combine(_date, datetime.min.time())