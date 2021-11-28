# -*- coding: utf-8 -*-
"""Retrieves and stores data in a local sqlite database

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

def create_midnight_datetime_from_date(_date: date) -> datetime:
    return datetime.combine(_date, datetime.min.time())

def get_empty_ohlcv_df():
    return pd.DataFrame(columns=DATAFRAME_HEADERS).set_index(INDEX_HEADER)

class DataPuller:

    def __init__(self, stored_retriever: Type[retrievers.OHLCVDataRetriever]=None, online_retriever: Type[retrievers.OHLCVDataRetriever]=None, database: Type[dbi.OHLCVDatabaseInterface]=None):
        self.stored_retriever = stored_retriever
        self.online_retriever = online_retriever
        self.database = database

    @classmethod
    def use_defaults(cls):
        database = dbi.SQLite3OHLCVDatabase()
        stored_retriever = retrievers.DatabaseRetriever(database)
        online_retriever = retrievers.CCXTDataRetriever('binance')
        return cls(stored_retriever, online_retriever, database)

    def fetch_df(self, symbol: str, timeframe_str: str, from_date_str: str, to_date_str: str=None):
        """grabs a pandas dataframe from the stored database if possible and from online otherwise"""
        symbol = symbol
        timeframe = Timeframe.from_string(timeframe_str)
        from_date = parser.parse(from_date_str).date()
        to_date = parser.parse(to_date_str).date() if to_date_str else datetime.utcnow().date() - timedelta(days=1)
        all_data = get_empty_ohlcv_df()

        #retrieve data from stored database if we have one
        if self.stored_retriever:
            all_data = self.stored_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        all_data = self.pull_missed_data(all_data, symbol, timeframe, from_date, to_date)

        return all_data

    def pull_missed_data(self, stored_data: pd.DataFrame, symbol: str, timeframe: Timeframe, from_date: date, to_date: date):
        """pull any missing data from self.online_retriever"""
        all_data = stored_data
        prior_pull_end_date = self._get_new_end_date(all_data, from_date)
        if prior_pull_end_date:
            online_data = self.online_pull(symbol, timeframe, from_date, prior_pull_end_date)
            all_data = all_data.append(online_data).sort_index()

        post_pull_from_date = self._get_new_from_date(all_data, to_date)
        if post_pull_from_date:
            online_data = self.online_pull(symbol, timeframe, post_pull_from_date, to_date)
            all_data = all_data.append(online_data).sort_index()
        return all_data

    def online_pull(self, symbol: str, timeframe: Timeframe, from_date: date, to_date: date):
        """perform a data pull from the online_retriever"""
        if not self.online_retriever:
            return get_empty_ohlcv_df()
        online_data = self.online_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)
        self.store_dataframe(online_data, timeframe)
        return online_data

    def store_dataframe(self, data: pd.DataFrame, timeframe: Timeframe):
        if self.database:
            self.database.store_dataframe(data, timeframe)

    def _get_new_end_date(self, data: pd.DataFrame, from_date: date):
        """returns the new end_date if a prior data pull is necessary"""
        check_date = create_midnight_datetime_from_date(from_date)
        if data.empty:
            return from_date
        if check_date not in data.index:
            return min(data.index) - timedelta(days=1)
        return None


    def _get_new_from_date(self, data: pd.DataFrame, to_date: date):
        """returns the new from_date if a post data pull is necessary"""
        check_date = create_midnight_datetime_from_date(to_date)
        if data.empty:
            return to_date
        if check_date not in data.index:
            return max(data.index) + timedelta(days=1)
        return None


if __name__ == '__main__':
    symbol = 'ETH/BTC'
    timeframe_str = '1h'
    from_date_str = '12-1-2020'
    to_date_str = '12-20-2020'
    puller = DataPuller.use_defaults()

    result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)
    

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
   


