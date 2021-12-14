import unittest
from unittest.mock import patch
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
from datetime import datetime,timedelta
import os
import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
from dateutil import parser
from pathlib import Path
from unittest.mock import MagicMock

#would be best to make this use "mock" to get api values without calling
PERFORM_API_TESTS = False



class TestMain(unittest.TestCase):

    def setUp(self):
        self.sqlite_database = dbi.SQLite3OHLCVDatabase(test=True)
        self.sqlite_database = dbi.SQLite3OHLCVDatabase(test=True)
        if os.path.exists(self.sqlite_database.get_database_file()):
            os.remove(self.sqlite_database.get_database_file())

        self.sqlite_retriever = retrievers.DatabaseRetriever(self.sqlite_database)
        self.ccxt_retriever = retrievers.CCXTDataRetriever('binance')
        self.file_path_1h = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-12-1_to_2020-12-20.csv'
        self.csv_retriver_1h = retrievers.CSVDataRetriever(self.file_path_1h)
        self.file_path_1d = str(Path(__file__).parent) + '\ETH_BTC_1D_2020-12-1_to_2020-12-20.csv'
        self.csv_retriver_1d = retrievers.CSVDataRetriever(self.file_path_1d)
    
    def test_main_online(self):
        """test pulling data from online source"""
        if not PERFORM_API_TESTS:
            return
        puller = gcd.DataPuller(online_retriever=self.ccxt_retriever)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'

        result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)

        expected = pd.read_csv(self.file_path_1h, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, result)


    def test_main_retrive_and_stored(self):
        """verify we pull stored data even when an online retriever is available"""
        csv_puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h, database=self.sqlite_database)
        stored_puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h,
                                       stored_retriever=self.sqlite_retriever,
                                       database=self.sqlite_database)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'
        
        csv_result = csv_puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)
        #below we force the csv retriever to return blank because it shouldn't be called at all. This verifies we
        #use the stored retriever only when all the data we are requesting is available for the stored retriever
        with patch('rba_tools.retriever.get_crypto_data.retrievers.CSVDataRetriever.fetch_ohlcv', return_value=gcd.get_empty_ohlcv_df()):
            stored_result = stored_puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)


        expected = pd.read_csv(self.file_path_1h, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, csv_result)
        pd.testing.assert_frame_equal(stored_result, csv_result)

    def test_main_multiple_timeframe(self):
        """test retrieving data from a period in which multiple timeframes of data exist"""
        csv_puller_1h = gcd.DataPuller(online_retriever=self.csv_retriver_1h, database=self.sqlite_database)
        stored_puller = gcd.DataPuller(stored_retriever=self.sqlite_retriever, database=self.sqlite_database)
        csv_puller_1d = gcd.DataPuller(online_retriever=self.csv_retriver_1d, database=self.sqlite_database)

        symbol = 'ETH/BTC'
        timeframe_str_1h = '1h'
        timeframe_str_1d = '1d'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'
        
        #fetch the data so it is stored on the database
        csv_result_1h = csv_puller_1h.fetch_df(symbol, timeframe_str_1h, from_date_str, to_date_str)
        csv_result_1d = csv_puller_1d.fetch_df(symbol, timeframe_str_1d, from_date_str, to_date_str)
        #retrieve the stored data while having multiple timeframes in that date range
        stored_result_1d = stored_puller.fetch_df(symbol, timeframe_str_1d, from_date_str, to_date_str)
        stored_result_1h = stored_puller.fetch_df(symbol, timeframe_str_1h, from_date_str, to_date_str)

        expected_1h = pd.read_csv(self.file_path_1h, parse_dates=True, index_col='Timestamp')
        expected_1d = pd.read_csv(self.file_path_1d, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected_1h, stored_result_1h)
        pd.testing.assert_frame_equal(expected_1d, stored_result_1d)

    def test_main_data_store_retrieve_prior(self):
        """verify that we pull prior and later data if we have middle data stored"""
        csv_puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h, database=self.sqlite_database)
        puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h,
                                       stored_retriever=self.sqlite_retriever,
                                       database=self.sqlite_database)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        full_from_date_str = '12-1-2020'
        full_to_date_str = '12-20-2020'
        partial_from_date_str = '12-5-2020'
        partial_to_date_str = '12-10-2020'
        
        #fetch the middle data so it is stored on the database
        csv_result = csv_puller.fetch_df(symbol, timeframe_str, partial_from_date_str, partial_to_date_str)
        #retrieve the stored data while having multiple timeframes in that date range
        
        result = puller.fetch_df(symbol, timeframe_str, full_from_date_str, full_to_date_str)
        expected = pd.read_csv(self.file_path_1h, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, result)

    def test_main_data_store_retrieve_prior_verify_call(self):
        """identical to above test but here we verify that calls have been made"""
        csv_puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h, database=self.sqlite_database)
        puller = gcd.DataPuller(online_retriever=self.csv_retriver_1h,
                                       stored_retriever=self.sqlite_retriever,
                                       database=self.sqlite_database)

        day = timedelta(days=1)
        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        tf = Timeframe.from_string(timeframe_str)
        full_from_date_str = '12-1-2020'
        full_from_date = parser.parse(full_from_date_str).date()
        full_to_date_str = '12-20-2020'
        full_to_date = parser.parse(full_to_date_str).date()
        partial_from_date_str = '12-5-2020'
        partial_from_date = (parser.parse(partial_from_date_str) - day).date()
        partial_to_date_str = '12-10-2020'
        partial_to_date = (parser.parse(partial_to_date_str) + day).date()
        
        
        #fetch the middle data so it is stored on the database
        csv_result = csv_puller.fetch_df(symbol, timeframe_str, partial_from_date_str, partial_to_date_str)
        #retrieve the stored data while having multiple timeframes in that date range
        puller.online_pull = MagicMock(return_value=gcd.get_empty_ohlcv_df())
        result = puller.fetch_df(symbol, timeframe_str, full_from_date_str, full_to_date_str)

        puller.online_pull.assert_any_call(symbol, tf, full_from_date, partial_from_date)
        puller.online_pull.assert_called_with(symbol, tf, partial_to_date, full_to_date)


if __name__ == "__main__":
    unittest.main()