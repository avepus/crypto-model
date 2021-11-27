# -*- coding: utf-8 -*-
"""Retrives and stores data in a local sqlite database

Created on Sat Apr 25 22:09:42 2020

@author: Avery

"""
from typing import Type
import ccxt
from datetime import datetime, date, timedelta
from dateutil import parser,tz
from rba_tools.retriever.timeframe import Timeframe
import rba_tools.retriever.database_interface as dbi
import rba_tools.retriever.retrievers as retrievers
from rba_tools.utils import convert_timeframe_to_ms
import pandas as pd

DATAFRAME_HEADERS = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol', 'Is_Final_Row']
INDEX_HEADER = 'Timestamp'

def get_empty_ohlcv_df():
    return pd.DataFrame(columns=DATAFRAME_HEADERS).set_index(INDEX_HEADER)


def main(symbol: str, timeframe_str: str, from_date_str: str, to_date_str: str=None, stored_retriever: Type[retrievers.OHLCVDataRetriever]=None, online_retriever: Type[retrievers.OHLCVDataRetriever]=None, database: Type[dbi.OHLCVDatabaseInterface]=None):
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
    database = dbi.SQLite3OHLCVDatabase()
    stored_retriver = retrievers.DatabaseRetriever(database)
    online_retriver = retrievers.CCXTDataRetriever('binance')

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
    retrievers = retrievers.CCXTDataRetriever('binance')
    result = retrievers.fetch_ohlcv(symbol, timeframe, from_date, to_date)
