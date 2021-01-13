# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 22:09:42 2020

@author: Avery And Jake
Together :')


"""

import ccxt
import pandas as pd
import numpy as np
import numpy
from time import sleep
from datetime import datetime, timedelta, timezone
from dateutil import parser,tz
import glob
import database
import sqlite3

#global variables
saved_data_directory = 'ohlcv_data\\'

def getBinanceExchange():
    """Gets ccxt class for binance exchange"""
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        'timeout': 30000,
        'enableRateLimit': True,
        })


def fetch_ohlcv_dataframe_from_exchange(symbol, exchange=None, timeFrame = '1d', start_time_ms=None, last_request_time_ms=None):
    """
    Attempts to retrieve data from an exchange for a specified symbol
    
    Returns data in a pandas dataframe
    Parameters:
        symbol (str) -- symbol to gather market data on (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from. Default is binance
        timeFrame (str) -- timeframe for which to retrieve the data
        start_time_ms (int) -- UTC timestamp in milliseconds
        last_request_time_ms (timestamp ms) -- timestamp of last call used to throttle number of calls
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


def get_DataFrame(symbol_list, exchange=None, from_date_str='1/1/1970', end_date_str='1/1/2050', ret_as_list=False, filename = "MarketData", timeframe = '1d', max_calls=10):
    """gets a dataframe in the expected format
    
    Parameters:
        symbol_list (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from
        from_date_str (str) -- string representation of start date timeframe
        end_date_str (str) -- string representation of end date timeframe
        ret_as_list (bool) -- boolean indicating to return list of dfs or single df
        fileName (str) -- beginning of the file name
        timeFrame (str) -- timeframe to pull
        maxCalls (int) -- max number of data pulls for a given currency
                            intended for use as safety net to prevent too many calls
    """
    if ret_as_list:
        return_df = []
    else:
        return_df = pd.DataFrame()
    connection = database.create_connection()
    df = get_saved_data(symbol_list, connection, from_date_str, end_date_str)

    from_date = parser.parse(from_date_str)
    end_date = parser.parse(end_date_str)

    for symbol in symbol_list:
        symbol_df = df.loc[df['Symbol'] == symbol]
        #left off here. need to implement only pulling needed data
        if symbol_df.empty and exchange is not None and from_date_str is not None:
            symbol_df = retrieve_data_from_exchange(symbol, exchange, from_date_str, end_date_str, timeframe, max_calls)
            if symbol_df.empty:
                print('Failed to retrieve',symbol,'data')
                continue
            symbol_df = populate_first_final(symbol_df)
            symbol_df.to_sql('OHLCV_DATA', connection, if_exists='append')
            symbol_df.index = pd.to_datetime(symbol_df.index, unit='ms')
            #save_data(df, symbol, filename)
        else:
            first_df_date = symbol_df.index.min()
            need_prior_data = first_df_date != from_date and symbol_df.at[first_df_date,'Is_Final_Row'] != 1
            last_df_date = symbol.df.index.max()
            need_later_data = last_df_date != end_date and symbol_df.at[last_df_date,'Is_Final_Row'] != 1
            #left off here. need to pull data
        return_df = return_df.append(df)
    connection.close()
    return return_df


def populate_is_final_column(df, from_date_ms, end_date_ms):
    if from_date_ms < df.index.min():
        df.at[df.index.min(),'Is_Final_Row'] = 1
    two_days_ms = 2 * 24 * 60 * 60 * 1000
    end_date_is_older_than_two_days = end_date_ms < (convert_datetime_to_UTC_Ms() - two_days_ms)
    if df.index.max() < end_date_ms and end_date_is_older_than_two_days:
        df.at[df.index.max(),'Is_Final_Row'] = 1
    return df

def retrieve_data_from_exchange(symbol, exchange, from_date, end_date=None, timeframe = '1d', max_calls=10):
    from_date_ms = convert_datetime_to_UTC_Ms(get_UTC_datetime(from_date))
    end_date_ms = convert_datetime_to_UTC_Ms(get_UTC_datetime(end_date))
    sleep(exchange.rateLimit / 1000)
    call_count = 1
    print('Fetching',symbol,'market data from',exchange,'. call #',call_count,sep='')
    df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, from_date_ms)
    if df.empty:
        print('Failed to retrieve',symbol,'data')
        return pd.DataFrame()
    retdf = df
    while (len(df) == 500 and call_count < max_calls and retdf.index.max() < end_date_ms):
        call_count += 1
        new_from_date=df.index[-1]
        sleep(exchange.rateLimit / 1000)
        print('Fetching ',symbol,' market data. call #',call_count,sep='')
        df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, new_from_date)
        retdf = retdf.append(df)
    if len(df) == 500 and call_count >= max_calls and retdf.index.max() < end_date_ms:
        print('Maximum data retrivals (',max_calls,') hit.', sep='')
        return pd.DataFrame()
    populate_is_final_column(retdf, from_date_ms, end_date_ms)
    return retdf


def get_saved_data_old(symbol, from_date=None, end_date=None):
    symbol = symbol.replace('/', '')
    search_name = saved_data_directory + '*' + symbol + '.csv'
    try:
        file = glob.glob(search_name)[0]
    except IndexError:
        return pd.DataFrame()
    
    df = pd.read_csv(file)
    df = set_data_timestamp_index(df)
    return df.loc[from_date:end_date]
    
def get_saved_data(symbol_list, connection, start_date_str=None, end_date_str=None):
    symbol_condition = "Symbol in ('" + "','".join(symbol_list) + "')"
    start_condition = ''
    end_condition = ''
    if start_date_str:
        start_date = convert_datetime_to_UTC_Ms(get_UTC_datetime(start_date_str))
        start_condition = f'and TIMESTAMP >= {start_date}'
    if end_date_str:
        end_date = convert_datetime_to_UTC_Ms(get_UTC_datetime(end_date_str))
        end_condition = f'and TIMESTAMP <= {end_date}'
    query = f"""SELECT * FROM OHLCV_DATA 
        WHERE {symbol_condition}
        {start_condition}
        {end_condition}"""
    df = pd.DataFrame
    try:
        df = pd.read_sql_query(query, connection)
    except:
        print('Query failed: \n' + query)
    return set_data_timestamp_index(df)



def set_data_timestamp_index(df, col='Timestamp', unit='ms'):
    """converts column with lable "Timestamp" of a DataFrame
    to a datetime and makes it the index

    Args:
        df (DataFrame): Pandas dataframe

    Returns:
        DataFrame: new Pandas DataFrame with updated index
    """
    if df.empty:
        return df
    retdf = df.set_index('Timestamp')
    retdf.index = pd.to_datetime(retdf.index, unit=unit)
    return retdf


def save_data_old(df, symbol, filename, show_output=True):
    file = filename + symbol + ".csv"
    file = file.replace("/", "")
    file = saved_data_directory + file
    df.to_csv(file)
    if show_output:
        print('data saved successfully to "',file,'"',sep='')


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
    df = get_DataFrame(['VIB/BTC'], exchange, '1/1/20')
    print(df)