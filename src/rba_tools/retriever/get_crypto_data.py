# -*- coding: utf-8 -*-
"""Retrieves and stores data in a local sqlite database

Created on Sat Apr 25 22:09:42 2020

@author: Avery

"""
from typing import Type
from datetime import datetime, date, timedelta
from dateutil import parser
from rba_tools.retriever.timeframe import Timeframe
import rba_tools.retriever.database_interface as dbi
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.constants as constants
import pandas as pd


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
        timeframe = Timeframe.from_string(timeframe_str)
        from_date = parser.parse(from_date_str).date()
        to_date = parser.parse(to_date_str).date() if to_date_str else datetime.utcnow().date() - timedelta(days=1)
        all_data = constants.empty_ohlcv_df_generator()

        #retrieve data from stored database if we have one
        if self.stored_retriever:
            all_data = self.stored_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        all_data = self.pull_missed_data(all_data, symbol, timeframe, from_date, to_date)

        return all_data

    def pull_missed_data(self, stored_data: pd.DataFrame, symbol: str, timeframe: Timeframe, from_date: date, to_date: date):
        """pull any missing data from self.online_retriever"""
        all_data = stored_data
        prior_pull_end_date = self._get_new_end_date(all_data, from_date, to_date)
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
            return constants.empty_ohlcv_df_generator()
        online_data = self.online_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)
        self.store_dataframe(online_data, timeframe)
        return online_data

    def store_dataframe(self, data: pd.DataFrame, timeframe: Timeframe):
        if self.database:
            self.database.store_dataframe(data, timeframe)

    def _get_new_end_date(self, data: pd.DataFrame, from_date: date, to_date: date):
        """returns the new end_date if a prior data pull is necessary"""
        check_date = constants.create_midnight_datetime_from_date(from_date)
        if data.empty:
            return to_date
        if check_date not in data.index:
            return min(data.index) - timedelta(days=1)
        return None


    def _get_new_from_date(self, data: pd.DataFrame, to_date: date):
        """returns the new from_date if a post data pull is necessary"""
        check_date = constants.create_midnight_datetime_from_date(to_date)
        if data.empty:
            return None
        if check_date not in data.index:
            return max(data.index) + timedelta(days=1)
        return None


if __name__ == '__main__':
    pass
    # database = dbi.SQLite3OHLCVDatabase(test=True)
    # stored_retriever = retrievers.DatabaseRetriever(database)
    # online_retriever = retrievers.CCXTDataRetriever('binance')
    # puller = DataPuller(stored_retriever, online_retriever, database)

    # symbol = 'ETH/BTC'
    # timeframe_str = '1h'
    # from_date_str = '12-1-2020'
    # to_date_str = '12-20-2020'

    # result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)

    # file = r'C:\Users\Avery\Documents\GitHub\rba_tools_project\rba_tools\retriever\test\ETH_BTC_1H_2020-1-1.csv'
    # expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')


    # symbol = 'ETH/BTC'
    # timeframe_str = '1h'
    # from_date_str = '12-1-2020'
    # to_date_str = '12-20-2020'
    # puller = DataPuller.use_defaults()

    # result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)