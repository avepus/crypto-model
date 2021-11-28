from abc import ABC, abstractmethod
from typing import Type
import ccxt
import pandas as pd
import numpy as np
from time import sleep
from datetime import datetime, date, timedelta
from dateutil import tz
from rba_tools.retriever.timeframe import Timeframe
import rba_tools.retriever.database_interface as dbi
import rba_tools.retriever.get_crypto_data as gcd

class OHLCVDataRetriever(ABC):
    "pulls OHLCV data for a specific symbol, timeframe, and date range"

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: date, to_date: date) -> pd.DataFrame:
        """obtains OHLCV data"""

    def get_from_and_to_datetimes(self, from_date: date, to_date: date):
        from_datetime = gcd.create_midnight_datetime_from_date(from_date)
        #add one day minus 1 second to get all the data from the end_date. Need for timeframes < 1 day
        to_datetime = gcd.create_midnight_datetime_from_date(to_date) + timedelta(seconds = -1, days=1)
        return (from_datetime, to_datetime)

class CCXTDataRetriever(OHLCVDataRetriever):

    def __init__(self, exchange: str):
        exchange_class = getattr(ccxt, exchange)
        self.exchange = exchange_class({
                            'timeout': 30000,
                            'enableRateLimit': True,
                            })
    
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: date, to_date: date) -> pd.DataFrame:
        from_datetime, to_datetime = self.get_from_and_to_datetimes(from_date, to_date)
        from_date_ms = self._convert_datetime_to_UTC_Ms(from_datetime)
        to_date_ms = self._convert_datetime_to_UTC_Ms(to_datetime)
        data = self.get_all_ccxt_data(symbol, timeframe, from_date_ms, to_date_ms)
        return self.format_ccxt_returned_data(data, symbol, to_datetime)

    def format_ccxt_returned_data(self, data, symbol, to_date) -> pd.DataFrame:
        """formats the data pulled from ccxt into the expected format"""
        if not data:
            return gcd.get_empty_ohlcv_df()
        header = [gcd.INDEX_HEADER, 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(data, columns=header).set_index(gcd.INDEX_HEADER)
        df.index = pd.to_datetime(df.index, unit='ms')
        df['Symbol'] = symbol
        df['Is_Final_Row'] = np.nan
        return df.loc[:to_date].copy()

    def get_all_ccxt_data(self, symbol: str, timeframe: Timeframe, from_date_ms: int, to_date_ms: int):
        """pull ccxt data repeatedly until we have all data"""
        call_count = 1
        return_data = None
        to_date_is_found_or_passed = False
        while not to_date_is_found_or_passed:
            print(f'Fetching {symbol} market data from {self.exchange}. call #{call_count}')
            ccxt_timeframe = self._ccxt_timeframe_format(timeframe)
            data = self.exchange.fetch_ohlcv(symbol, ccxt_timeframe, since=from_date_ms)
            sleep(self.exchange.rateLimit / 1000)
            if not data: #handle when we don't get any data by returning what we have so far
                return return_data
            call_count += 1
            if return_data:
                return_data.extend(data)
            else:
                return_data = data
            to_date_is_found_or_passed = any(to_date_ms == row[0] or to_date_ms < row[0] for row in data)
            last_end_timestamp_ms = data[len(data) - 1][0]
            from_date_ms = last_end_timestamp_ms + 1 #add one to not grab same time twice
        return return_data

    def _ccxt_timeframe_format(self, timeframe: Timeframe):
        return timeframe.get_timeframe_name().lower()

    def _convert_datetime_to_UTC_Ms(self,input_datetime=None):
        return int(round(input_datetime.replace(tzinfo = tz.tzutc()).timestamp() * 1000))

class CSVDataRetriever(OHLCVDataRetriever):

    def __init__(self, file):
        self.file = file
        
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        from_datetime, to_datetime = self.get_from_and_to_datetimes(from_date, to_date)
        data = pd.read_csv(self.file, index_col=gcd.INDEX_HEADER, parse_dates=True)
        return self.format_csv_data(data, symbol, from_datetime, to_datetime)

    def format_csv_data(self, data, symbol: str, from_date: datetime, to_date: datetime):
        df = data.loc[data['Symbol'] == symbol]
        return df.loc[from_date:to_date].copy()

class DatabaseRetriever(OHLCVDataRetriever):
    """pulls data from a OHLCVDatabase database"""
    
    def __init__(self, database: Type[dbi.OHLCVDatabaseInterface]):
        self.database = database

    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        query = self.get_query(symbol, timeframe, from_date, to_date)
        query_result = self.database.get_query_result_as_dataframe(query, timeframe)
        return self.format_database_data(query_result)

    def format_database_data(self, data: pd.DataFrame):
        if data.empty:
            return data
        data[gcd.INDEX_HEADER] = pd.to_datetime(data[gcd.INDEX_HEADER])
        data['Is_Final_Row'] = pd.to_numeric(data['Is_Final_Row'], errors='coerce')
        return data.set_index(gcd.INDEX_HEADER)

    def get_query(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime):
        """Generate query based on fetch_ohlcv parameters"""
        to_date_plus_1 = to_date + timedelta(days=1)
        symbol_condition = "Symbol = '" + symbol + "'"
        table_name = timeframe.get_timeframe_table_name()
        start_condition = f'and {gcd.INDEX_HEADER} >= "{from_date}"'
        end_condition = f'and {gcd.INDEX_HEADER} < "{to_date_plus_1}"'
        return f"""SELECT * FROM {table_name} 
            WHERE {symbol_condition}
            {start_condition}
            {end_condition}"""