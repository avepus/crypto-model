# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 22:09:42 2020

@author: Avery And Jake
Together :')


"""

import ccxt
import pandas as pd
import numpy
from time import sleep
from datetime import datetime, timedelta, timezone
from dateutil import parser,tz
import glob

#global variables
saved_data_directory = 'ohlcv_data\\'

print("wowza")
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


def get_DataFrame(symbol_list, exchange=None, from_date=None, end_date=None, ret_as_list=True, filename = "MarketData", timeframe = '1d', max_calls=10):
    """gets a dataframe in the expected format
    
    Parameters:
        symbol_list (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from
        from_date (str) -- string representation of start date timeframe
        end_date (str) -- string representation of end date timeframe
        ret_as_list (bool) -- boolean indicating to return list of dfs or single df
        fileName (str) -- beginning of the file name
        timeFrame (str) -- timeframe to pull
        maxCalls (int) -- max number of data pulls for a given currency
    """
    if ret_as_list:
        return_df = []
    else:
        return_df = pd.DataFrame()
        
    for symbol in symbol_list:
        df = get_saved_data(symbol, from_date, end_date)
        if df.empty and exchange is not None and from_date is not None:
            df = retrieve_data_from_exchange(symbol, exchange, from_date, end_date, timeframe, max_calls)
            if not df.empty:
                save_data(df, symbol, filename)
        if df.empty: #enhancement is to call check_retrival_for_errors(df) for warnings/errors regarding data retrieval
            print('Failed to retrieve',symbol,'data')
        return_df.append(df)
    return return_df


def retrieve_data_from_exchange(symbol, exchange, from_date, end_date=None, timeframe = '1d', max_calls=10):
    from_date_as_ms_timestamp = convert_datetime_to_UTC_Ms(get_UTC_datetime(from_date))
    sleep(exchange.rateLimit / 1000)
    call_count = 1
    print('Fetching',symbol,'market data from',exchange,'. call #',call_count,sep='')
    df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, from_date_as_ms_timestamp)
    if df.empty:
        print('Failed to retrieve',symbol,'data')
        return pd.DataFrame()
    retdf = df
    while (len(df) == 500 and call_count < max_calls):
        call_count += 1
        new_from_date=df.index[-1]
        sleep(exchange.rateLimit / 1000)
        print('Fetching ',symbol,' market data. call #',call_count,sep='')
        df = fetch_ohlcv_dataframe_from_exchange(symbol, exchange, timeframe, new_from_date)
        retdf = retdf.append(df)
    #Commenting out becuase we wouldn't know at the current time of
    #evaluation if a currency is delisted in the future
    # if retdf.loc[includeStamp:,:].empty:
    #     print(symbol,'data did not include',includeDate,'data not saved.')
    #     if attempt >= maxCalls:
    #         print('Maximum data retrivals (',maxCalls,') hit.', sep='')
    #     continue
    return retdf


def get_saved_data(symbol, from_date=None, end_date=None):
    symbol = symbol.replace('/', '')
    search_name = saved_data_directory + '*' + symbol + '.csv'
    try:
        file = glob.glob(search_name)[0]
    except IndexError:
        return pd.DataFrame()
    
    df = pd.read_csv(file)
    df = set_data_timestamp_index(df)
    return df.loc[from_date:end_date]


def set_data_timestamp_index(df):
    col = None
    unit = None
    if ("Date" in df.columns):
        col = "Date"
    if ("Timestamp" in df.columns):
        col = "Timestamp"
        unit = 'ms'
    df.loc[:,col] = pd.to_datetime(df.loc[:,col], unit=unit)
    if col is not None:
        return df.set_index(col)


def save_data(df, symbol, filename, show_output=True):
    file = filename + symbol + ".csv"
    file = file.replace("/", "")
    file = saved_data_directory + file
    df.to_csv(file)
    if show_output:
        print('data saved successfully to "',file,'"',sep='')


def get_UTC_datetime(datetime_string=None):
    if datetime_string is None:
        return convert_datetime_to_UTC_Ms()
    return parser.parse(datetime_string).replace(tzinfo = tz.tzutc())


def convert_datetime_to_UTC_Ms(input_datetime=None):
    if input_datetime is None:
        input_datetime = datetime.now()
    return int(round(input_datetime.replace(tzinfo = tz.tzutc()).timestamp() * 1000))
   

if __name__ == '__main__':
    exchange = getBinanceExchange()
    symbols = getAllSymbolsForQuoteCurrency("BTC", exchange)
    df = get_DataFrame(['ETH/BTC'], exchange, '7/1/18')
    print(df)