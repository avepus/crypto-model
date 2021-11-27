# -*- coding: utf-8 -*-
"""Retrives and stores data in a local sqlite database

Created on Sat Apr 25 22:09:42 2020

@author: Avery

"""
from abc import ABC, abstractmethod
from typing import Type
import ccxt
import pandas as pd
import numpy as np
from time import sleep
from datetime import datetime, date, timedelta
from dateutil import parser,tz
import rba_tools.retriver.database as database
from rba_tools.retriver.timeframe import Timeframe
from rba_tools.utils import convert_timeframe_to_ms,get_table_name_from_str,get_table_name_from_dataframe
import sqlite3
from pathlib import Path
from dataclasses import dataclass

DATAFRAME_HEADERS = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol', 'Is_Final_Row']
INDEX_HEADER = 'Timestamp'

def get_empty_ohlcv_df():
    return pd.DataFrame(columns=DATAFRAME_HEADERS).set_index(INDEX_HEADER)


class OHLCVDatabaseInterface(ABC):
    @abstractmethod
    def store_dataframe(self, df: pd.DataFrame, timeframe: Timeframe) -> None:
        """stores pandas dataframe data into database"""

    @abstractmethod
    def get_query_result_as_dataframe(self, query: str, timeframe: Timeframe) -> pd.DataFrame:
        """executes an SQL query and returns results in dataframe"""

class SQLite3OHLCVDatabase(OHLCVDatabaseInterface):

    def __init__(self, test=False):
        db_file = 'ohlcv_sqlite_test.db' if test else 'ohlcv_sqlite.db'
        self.database_file = str(Path(__file__).parent) + '\\ohlcv_data\\' + db_file
        self.connection = None
        
    def store_dataframe(self, df: pd.DataFrame, timeframe: Timeframe):
        self.create_OHLCV_table_if_not_exists(timeframe)
        connection = sqlite3.connect(self.get_database_file())
        table_name = timeframe.get_timeframe_table_name()
        try:
            df.to_sql(table_name, connection, if_exists='append')
        finally:
            connection.close()

    def get_query_result_as_dataframe(self, query: str, timeframe: Timeframe):
        self.create_OHLCV_table_if_not_exists(timeframe)
        connection = sqlite3.connect(self.get_database_file())
        result = get_empty_ohlcv_df()
        try:
            result = pd.read_sql_query(query, connection)
        finally:
            connection.close()
        return result

    def create_OHLCV_table_if_not_exists(self, timeframe: Timeframe) -> None:
        table_name = timeframe.get_timeframe_table_name()
        sql_create_ohlcv_table = f""" CREATE TABLE IF NOT EXISTS {table_name} (
                                        Timestamp integer NOT NULL,
                                        Open real NOT NULL,
                                        High real NOT NULL,
                                        Low real NOT NULL,
                                        Close real NOT NULL,
                                        Volume integer NOT NULL,
                                        Symbol string NOT NULL,
                                        Is_Final_Row integer,
                                        PRIMARY KEY (Symbol, Timestamp)
                                        CHECK(Is_Final_Row == 0 or Is_Final_Row == 1 or Is_Final_Row is NULL)
                                    ); """
        connection = sqlite3.connect(self.get_database_file())
        try:
            cursor = connection.cursor()
            cursor.execute(sql_create_ohlcv_table)
        finally:
            connection.close()

    def _execute_query(self, query: str):
        """execute and return data from a query. Meant only for troubleshooting"""
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            data = cursor.fetchall()
        finally:
            connection.close()
        return data

    def get_database_file(self):
        return self.database_file

class OHLCVDataRetriver(ABC):
    "pulls OHLCV data for a specific symbol, timeframe, and date range"

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: date, to_date: date) -> pd.DataFrame:
        """obtains OHLCV data"""

    def get_from_and_to_datetimes(self, from_date: date, to_date: date):
        from_datetime = datetime.combine(from_date, datetime.min.time())
        #add one day minus 1 second to get all the data from the end_date. Need for timeframes < 1 day
        to_datetime = datetime.combine(to_date, datetime.min.time()) + timedelta(seconds = -1, days=1)
        return (from_datetime, to_datetime)

class CCXTDataRetriver(OHLCVDataRetriver):

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
            return get_empty_ohlcv_df()
        header = [INDEX_HEADER, 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(data, columns=header).set_index(INDEX_HEADER)
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

class CSVDataRetriver(OHLCVDataRetriver):

    def __init__(self, file):
        self.file = file
        
    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        from_datetime, to_datetime = self.get_from_and_to_datetimes(from_date, to_date)
        data = pd.read_csv(self.file, index_col=INDEX_HEADER, parse_dates=True)
        return self.format_csv_data(data, symbol, from_datetime, to_datetime)

    def format_csv_data(self, data, symbol: str, from_date: datetime, to_date: datetime):
        df = data.loc[data['Symbol'] == symbol]
        return df.loc[from_date:to_date].copy()

class DatabaseRetriver(OHLCVDataRetriver):
    """pulls data from a OHLCVDatabase database"""
    
    def __init__(self, database: Type[OHLCVDatabaseInterface]):
        self.database = database

    def fetch_ohlcv(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        query = self.get_query(symbol, timeframe, from_date, to_date)
        query_result = self.database.get_query_result_as_dataframe(query, timeframe)
        return self.format_database_data(query_result)

    def format_database_data(self, data: pd.DataFrame):
        if data.empty:
            return data
        data[INDEX_HEADER] = pd.to_datetime(data[INDEX_HEADER])
        data['Is_Final_Row'] = pd.to_numeric(data['Is_Final_Row'], errors='coerce')
        return data.set_index(INDEX_HEADER)

    def get_query(self, symbol: str, timeframe: Timeframe, from_date: datetime, to_date: datetime):
        """Generate query based on fetch_ohlcv parameters"""
        symbol_condition = "Symbol = '" + symbol + "'"
        table_name = timeframe.get_timeframe_table_name()
        start_condition = f'and {INDEX_HEADER} >= "{from_date}"'
        end_condition = f'and {INDEX_HEADER} <= "{to_date}"'
        return f"""SELECT * FROM {table_name} 
            WHERE {symbol_condition}
            {start_condition}
            {end_condition}"""


def main(symbol: str, timeframe_str: str, from_date_str: str, to_date_str: str=None, stored_retriever: Type[OHLCVDataRetriver]=None, online_retriever: Type[OHLCVDataRetriver]=None, database: Type[OHLCVDatabaseInterface]=None):
    """retrieves a dataframe from saved database if possible otherwise from online"""
    timeframe = Timeframe.from_string(timeframe_str)

    from_date = parser.parse(from_date_str).date()
    if to_date_str:
        to_date = parser.parse(to_date_str).date()
    else:
        #default to_date to yesterday
        to_date = from_date.today() - timedelta(days=1)

    all_data = get_empty_ohlcv_df()
    online_data = get_empty_ohlcv_df()

    #retrieve data from stored database if we have one
    if stored_retriever:
        all_data = stored_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

    #pull extra data if we have one
    if online_retriever:
        prior_pull_end_date = needs_former_data(all_data, from_date)
        if prior_pull_end_date:
            online_data = online_retriever.fetch_ohlcv(symbol, timeframe, from_date, prior_pull_end_date)
            database.store_dataframe(online_data, timeframe)
            all_data = all_data.append(online_data).sort_index()

        post_pull_from_date = needs_later_data(all_data, to_date)
        if post_pull_from_date:
            online_data = online_retriever.fetch_ohlcv(symbol, timeframe, post_pull_from_date, to_date)
            database.store_dataframe(online_data, timeframe)
            all_data = all_data.append(online_data).sort_index()

    return all_data

def needs_former_data(data: pd.DataFrame, from_date: date):
    """returns the new end_date if a prior data pull is necessary"""
    if data.empty:
        return from_date
    if from_date not in data.index:
        return min(data.index) - timedelta(days=1)
    return None


def needs_later_data(data: pd.DataFrame, to_date: date):
    """returns the new from_date if a post data pull is necessary"""
    if data.empty:
        return to_date
    if to_date not in data.index:
        return min(data.index) + timedelta(days=1)
    return None
    
def main_default(symbol: str, timeframe_str: str, from_date_str: str, to_date_str: str=None):
    """calls main method with some defaults"""
    database = SQLite3OHLCVDatabase()
    stored_retriver = DatabaseRetriver(database)
    online_retriver = CCXTDataRetriver('binance')

    return main(symbol, timeframe_str, from_date_str, to_date_str, stored_retriver, online_retriver, database)



    

#old code below
###########################################################


def getBinanceExchange():
    """Gets ccxt class for binance exchange"""
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        'timeout': 30000,
        'enableRateLimit': True,
        })


def getAllTickers(exchange):
    if not exchange.has['fetchTickers']:
        print("Exchange cannot fetch all tickers")
    else:
        return exchange.fetch_tickers()


def getAllSymbolsForQuoteCurrency(quoteSymbol, exchange):
    """
    Get's list of all currencies with the input quote currency
    
    Returns a list
    Parameters:
        quoteSymbol (str) -- symbol to check base curriencies for (e.g. "BTC")
        exchange (ccxt class) -- ccxt excahnge to retrieve data from
    """
    if "/" not in quoteSymbol:
        quoteSymbol = "/" + quoteSymbol
    ret = []
    allTickers = exchange.fetch_tickers()
    for symbol in allTickers:
        if quoteSymbol in symbol:
            ret.append(symbol)
    return ret


def populate_is_final_column(df, from_date_ms, end_date_ms, timeframe):
    """populates Is_Final_Column to indicate that no past or future data
    exists past that row
    
    Parameters:
        df (DataFrame) -- dataframe for which to popualte the column
        from_date_ms (int) -- from date in milliseconds
        end_date_ms (int) -- end date in milliseconds
        timeframe (str) -- timeframe that data is in (e.g. 1h, 1d, 1m, etc.)
    
    Returns:
        DataFrame: updated DataFrame (note the input DataFrame is modified)
    """
    #if our from date is less than one bar behind our earliest data then there is no previous data
    timeframe_ms = convert_timeframe_to_ms(timeframe)
    if from_date_ms < (df.index.min().item() - timeframe_ms): 
        df.at[df.index.min(),'Is_Final_Row'] = 1
    two_timeframes_ms = 2 * timeframe_ms
    end_date_is_older_than_two_timeframes = end_date_ms < (convert_datetime_to_UTC_Ms() - two_timeframes_ms)
    #if our end date is greater than one bar past our latest data then this is no future data
    if end_date_ms > (df.index.max() + timeframe_ms) and end_date_is_older_than_two_timeframes:
        df.at[df.index.max(),'Is_Final_Row'] = 1
    return df
    

def get_UTC_datetime(datetime_string=None):
    if datetime_string is None:
        return datetime.now()
    return parser.parse(datetime_string).replace(tzinfo = tz.tzutc())


def convert_datetime_to_UTC_Ms(input_datetime=None):
    if input_datetime is None:
        input_datetime = datetime.now()
    return int(round(input_datetime.replace(tzinfo = tz.tzutc()).timestamp() * 1000))
   

if __name__ == '__main__':
    symbol = 'ETH/BTC'
    timeframe = '1d'
    from_date = datetime(2019, 12, 1)
    to_date = datetime(2021, 12, 3)
    retriver = CCXTDataRetriver('binance')
    result = retriver.fetch_ohlcv(symbol, timeframe, from_date, to_date)
