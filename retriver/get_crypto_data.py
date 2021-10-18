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
from datetime import datetime, timedelta, timezone
from dateutil import parser,tz
import rba_tools.retriver.database as database
from rba_tools.utils import convert_timeframe_to_ms
import sqlite3

timeframe_map_ms = {
        'm': 60000,
        'h': 3600000,
        'd': 86400000,
        'w': 86400000*7
    }

def getBinanceExchange():
    """Gets ccxt class for binance exchange"""
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        'timeout': 30000,
        'enableRateLimit': True,
        })


def get_empty_ohlcv_df():
    return pd.DataFrame(columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume','Symbol','Is_Final_Row']).set_index('Timestamp')

class OHLCVDataRetriver(ABC):
    "pulls OHLCV data for a specific symbol, timeframe, and date range"

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeFrame: str, from_date: datetime, to_date: datetime = None) -> Type[pd.DataFrame]:
        """obtains OHLCV data"""


class CCXTDataRetriver(OHLCVDataRetriver):

    def __init__(self, exchange: str):
        exchange_class = getattr(ccxt, exchange)
        self.exchange = exchange_class({
                            'timeout': 30000,
                            'enableRateLimit': True,
                            })
    
    def fetch_ohlcv(self, symbol: str, timeFrame: str, from_date: datetime, to_date: datetime) -> Type[pd.DataFrame]:
        from_date_ms = convert_datetime_to_UTC_Ms(from_date)
        data = self.exchange.fetch_ohlcv(symbol, timeFrame, since=from_date_ms)
        return self.format_ccxt_returned_data(data, symbol)

    def format_ccxt_returned_data(self,data, symbol) -> Type[pd.DataFrame]:
        """formats the data pulled from ccxt into the expected format"""
        header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        df = pd.DataFrame(data, columns=header).set_index('Timestamp')
        df.index = pd.to_datetime(df.index, unit='ms')
        df['Symbol'] = symbol
        df['Is_Final_Row'] = np.nan
        return df

class SQLite3DatabaseRetriver(OHLCVDataRetriver):
    """pulls data from an sqlite3 database"""
    pass

class OHLCVDataStoreer(ABC):
    """saves OHLCV data"""

    @abstractmethod
    def save_ohlcv(self, OHLCVDatabase):
        """saves OHLCV data"""


def fetch_ohlcv_dataframe_from_exchange(symbol, exchange=None, timeFrame = '1d', start_time_ms=None, last_request_time_ms=None):
    """
    testAttempts to retrieve data from an exchange for a specified symbol
    
    Returns data retrieved from ccxt exchange in a pandas dataframe
    with Symbol and Is_Final_Row columns
    Parameters:
        symbol (str) -- symbol to gather market data on (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from. Default is binance
        timeFrame (str) -- timeframe for which to retrieve the data
        start_time_ms (int) -- UTC timestamp in milliseconds
        last_request_time_ms (timestamp ms) -- timestamp of last call used to throttle number of calls
    
    Returns:
        DataFrame: retrived data in Pandas DataFrame with ms timestamp index
    """
    if type(start_time_ms) == str:
        start_time_ms = convert_datetime_to_UTC_Ms(get_UTC_datetime(start_time_ms))
    if exchange is None:
        exchange = getBinanceExchange()
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    if not exchange.has['fetchOHLCV']:
        print(exchange, "doesn't support fetchOHLCV")
        return pd.DataFrame([], columns=header) #empty dataframe
    now = convert_datetime_to_UTC_Ms()
    if last_request_time_ms is not None and (now - last_request_time_ms) < 1000:
        sleep(1000 - (now - last_request_time_ms))
    last_request_time_ms = convert_datetime_to_UTC_Ms()
    print('lastCall =',last_request_time_ms,'fetching data...')
    data = exchange.fetch_ohlcv(symbol, timeFrame, since=start_time_ms)
    df = pd.DataFrame(data, columns=header).set_index('Timestamp')
    df['Symbol'] = symbol
    df['Is_Final_Row'] = np.nan
    return df


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


def get_DataFrame(symbol_list, exchange=None, from_date_str='1/1/1970', end_date_str='1/1/2050', ret_as_list=False, timeframe = '1d', max_calls=10):
    """gets a dataframe in the expected format
    
    Parameters:
        symbol_list (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from
        from_date_str (str) -- string representation of start date timeframe
        end_date_str (str) -- string representation of end date timeframe
        ret_as_list (bool) -- boolean indicating to return list of dfs or single df
        timeFrame (str) -- timeframe to pull in string format like '3h'
        maxCalls (int) -- max number of data pulls for a given currency
                            intended for use as safety net to prevent too many calls

    Returns:
        DataFrame: retrived data in Pandas DataFrame with ms timestamp index
    """
    if ret_as_list:
        return_df = []
    else:
        return_df = pd.DataFrame()
    with database.OHLCVDatabase() as connection:
        df = get_saved_data(symbol_list, connection, from_date_str, end_date_str, timeframe=timeframe) 

    from_date = parser.parse(from_date_str)
    end_date = parser.parse(end_date_str)

    from_date_ms = convert_datetime_to_UTC_Ms(from_date)
    end_date_ms = convert_datetime_to_UTC_Ms(end_date)

    for symbol in symbol_list:
        symbol_df = df.loc[df['Symbol'] == symbol] #grab just this symbol data since they're all in one dataframe
        if symbol_df.empty and exchange is not None:
            symbol_df = retrieve_data_from_exchange(symbol, exchange, from_date_ms, end_date_ms, timeframe, max_calls)
            if symbol_df.empty:
                print('Failed to retrieve',symbol,'data')
                continue
            symbol_df.to_sql('OHLCV_DATA', connection, if_exists='append')
            symbol_df.index = pd.to_datetime(symbol_df.index, unit='ms')

        elif exchange is not None:
            first_df_timestamp = symbol_df.index.min().item() #.item() gets us the native python number type instead of the numpy type
            need_prior_data = (first_df_timestamp != from_date_ms) and (symbol_df.at[first_df_timestamp,'Is_Final_Row'] != 1)
            if need_prior_data:
                first_df_timestamp -= 1 #we subtract 1 to the timestamp to pull the up to this timestamp which avoids duplicates
                first_df_timestamp_str = datetime.fromtimestamp(first_df_timestamp / 1000, tz.tzutc())
                print(f'Need earlier data for {symbol}. Retreiving data from {from_date_str} ({from_date_ms}) to {first_df_timestamp_str} ({first_df_timestamp})')
                prior_data = retrieve_data_from_exchange(symbol, exchange, from_date_ms, first_df_timestamp, timeframe, max_calls)
                prior_data.to_sql('OHLCV_DATA', connection, if_exists='append')
                symbol_df = symbol_df.append(prior_data).sort_index() #we sort index when appending prior data so it doesn't append to the end

            last_df_timestamp = symbol_df.index.max().item()
            two_days_ms = 2 * 24 * 60 * 60 * 1000
            last_timestamp_is_older_than_two_days = last_df_timestamp < (convert_datetime_to_UTC_Ms() - two_days_ms)
            need_later_data = last_df_timestamp != end_date_ms and symbol_df.at[last_df_timestamp,'Is_Final_Row'] != 1 and last_timestamp_is_older_than_two_days
            if need_later_data:
                last_df_timestamp += 1 #we add 1 to the timestamp to pull the next timestamp data and to avoid duplicates
                last_df_timestamp_str = datetime.fromtimestamp(last_df_timestamp / 1000, tz.tzutc())
                print(f'Need later data for {symbol}. Retreiving data from {last_df_timestamp_str} ({last_df_timestamp}) to {end_date_str} ({end_date_ms})')
                later_data = retrieve_data_from_exchange(symbol, exchange, last_df_timestamp, end_date_ms, timeframe, max_calls)
                later_data.to_sql('OHLCV_DATA', connection, if_exists='append')
                symbol_df = symbol_df.append(later_data)

        else:
            raise NameError('Data is missing for',symbol,'but no exchange was passed in to retrieve data from')
        if ret_as_list:
            return_df.append(set_data_timestamp_index(symbol_df))
        else:
            return_df = return_df.append(set_data_timestamp_index(symbol_df))
    connection.close()
    return return_df


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
    

def retrieve_data_from_exchange(symbol, exchange, from_date_ms, end_date_ms=None, timeframe = '1d', max_calls=10):
    """Retrives data from ccxt exchange
    
    pulls data from ccxt exchange in 500 bar increments until we have all the data
    betwen from_date_ms and end_date_ms or we hit max_calls. Also calls
    populate_is_final_column to populate the Is_Final_Column of the DataFrame
    Parameters:
        symbol_list (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from
        from_date_ms (int) -- from date in utc milliseconds
        end_date_ms (int) -- end date in utc milliseconds
        timeFrame (str) -- timeframe to pull (e.g. '1d' for day)
        maxCalls (int) -- max number of data pulls for a given currency
                            intended for use as safety net to prevent too many calls
    
    Returns:
        DataFrame: retrived data in Pandas DataFrame with ms timestamp index
    """
    if not end_date_ms:
        convert_datetime_to_UTC_Ms()
    sleep(exchange.rateLimit / 1000)
    call_count = 1
    print(f'Fetching {symbol} market data from {exchange}. call #{call_count}')
    df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, from_date_ms)
    if df.empty:
        print('Failed to retrieve',symbol,'data')
        return pd.DataFrame()
    retdf = df
    while (len(df) == 500 and call_count < max_calls and retdf.index.max() < end_date_ms):
        call_count += 1
        new_from_date = df.index[-1].item() + 1 #add 1 to prevent retrival of the same date
        sleep(exchange.rateLimit / 1000)
        print(f'Fetching {symbol} market data from {exchange}. call #{call_count}')
        df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, new_from_date)
        retdf = retdf.append(df)
    if len(df) == 500 and call_count >= max_calls and retdf.index.max() < end_date_ms:
        print(f'Maximum data retrivals ({max_calls}) hit.')
        return pd.DataFrame()
    populate_is_final_column(retdf, from_date_ms, end_date_ms, timeframe)
    return retdf.loc[from_date_ms:end_date_ms,:]
    

def get_saved_data(symbol_list, connection, from_date_str=None, end_date_str=None, timeframe=None):
    """Attempts to retrive data from saved database
    
    Parameters:
        symbol_list (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        connection (obj) -- connectiont to sql database
        from_date_str (str) -- string representation of start date timeframe
        end_date_str (str) -- string representation of end date timeframe
        timeFrame (str) -- timeframe to pull in string format like '3h'

    Returns:
        DataFrame: retrived data in Pandas DataFrame with ms timestamp index
    """
    comma_symbols = "','".join(symbol_list)
    symbol_condition = "Symbol in ('" + comma_symbols + "')"
    start_condition = ''
    end_condition = ''
    timeframe_condition = ''
    if from_date_str:
        start_date = convert_datetime_to_UTC_Ms(get_UTC_datetime(from_date_str))
        start_condition = f'and TIMESTAMP >= {start_date}'
    if end_date_str:
        end_date = convert_datetime_to_UTC_Ms(get_UTC_datetime(end_date_str))
        end_condition = f'and TIMESTAMP <= {end_date}'
    if timeframe:
        timeframe_ms = convert_timeframe_to_ms(timeframe)
        timeframe_condition = f'and TIMESTAMP % {timeframe_ms} = 0'
    query = f"""SELECT * FROM OHLCV_DATA 
        WHERE {symbol_condition}
        {start_condition}
        {end_condition}
        {timeframe_condition}"""
    try:
        df = pd.read_sql_query(query, connection)
    except Exception as e:
        print('Query failed: \n' + query)
        print(e)
        return get_empty_ohlcv_df()
    df['Is_Final_Row'] = pd.to_numeric(df['Is_Final_Row'], errors='coerce')
    df.set_index('Timestamp', inplace=True)
    return trim_data_outside_timeframe(df, timeframe) 

def trim_data_outside_timeframe(df, timeframe):
    """Removes rows from dataframe that are not in the timeframe
    
    Parameters:
        df (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        timeframe (str) -- timeframe to pull in string format like '3h'

    Returns:
        DataFrame: with non-timeframe rows removed
    """
    timeframe_ms = convert_timeframe_to_ms(timeframe)
    #get series of rows that are in the timeframe based on difference between rows
    in_timeframe_bool_series = df.index.to_series().diff() == timeframe_ms
    #the first row gets missed by the above line so this corrects that
    if df.empty:
        return df
    try:
        first_true = min(in_timeframe_bool_series.loc[in_timeframe_bool_series].index)
    except ValueError:
        return get_empty_ohlcv_df()
    in_timeframe_bool_series[in_timeframe_bool_series.index < first_true] = True
    return df.loc[in_timeframe_bool_series].copy()

def set_data_timestamp_index(df, col='Timestamp', unit='ms'):
    """converts column with lable "Timestamp" of a DataFrame
    to a datetime and makes it the index

    Args:
        df (DataFrame): Pandas dataframe

    Returns:
        DataFrame: new Pandas DataFrame with updated index
    """
    retdf = df.copy()
    if retdf.empty:
        return retdf
    if retdf.index.name != 'Timestamp':
        retdf = retdf.set_index('Timestamp')
    retdf.index = pd.to_datetime(retdf.index, unit=unit)
    return retdf


def get_UTC_datetime(datetime_string=None):
    if datetime_string is None:
        return datetime.now()
    return parser.parse(datetime_string).replace(tzinfo = tz.tzutc())


def convert_datetime_to_UTC_Ms(input_datetime=None):
    if input_datetime is None:
        input_datetime = datetime.now()
    return int(round(input_datetime.replace(tzinfo = tz.tzutc()).timestamp() * 1000))
   

if __name__ == '__main__':
    exchange = getBinanceExchange()
    #symbols = getAllSymbolsForQuoteCurrency("BTC", exchange)
    #df = get_DataFrame(['ETH/BTC'], exchange, '7/27/18', '7/29/20', timeframe='1h')
    #print(df)
    #first = get_DataFrame(['ETH/BTC'], exchange, '12/1/20', '12/3/20', timeframe='1h')
    connection = database.create_connection()

    df = get_saved_data(['ETH/BTC'], connection, '12/1/20', '12/5/20', timeframe='4h')

    print(df)
    connection.close()