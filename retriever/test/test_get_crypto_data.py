import unittest
from unittest.mock import patch
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
from datetime import datetime
import os
import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
from dateutil import parser
from pathlib import Path

#would be best to make this use "mock" to get api values without calling
PERFORM_API_TESTS = False



class TestMain(unittest.TestCase):

    def setUp(self):
        """clear out test data if it exists"""
        db = dbi.SQLite3OHLCVDatabase(test=True)
        if os.path.exists(db.get_database_file()):
            os.remove(db.get_database_file())

        self.sqlite_database = dbi.SQLite3OHLCVDatabase(test=True)
        self.sqlite_retriever = retrievers.DatabaseRetriever(self.sqlite_database)
        self.ccxt_retriever = retrievers.CCXTDataRetriever('binance')
        file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
        self.csv_retriver = retrievers.CSVDataRetriever(file)
    
    def test_main_online(self):
        if not PERFORM_API_TESTS:
            return
        puller = gcd.DataPuller(online_retriever=self.ccxt_retriever)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'

        result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)

        file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
        expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, result)


    def test_main_retrive_and_stored(self):
        csv_puller = gcd.DataPuller(online_retriever=self.csv_retriver, database=self.sqlite_database)
        stored_puller = gcd.DataPuller(stored_retriever=self.sqlite_retriever, database=self.sqlite_database)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'

        with patch('rba_tools.retriever.get_crypto_data.retrievers.CSVDataRetriever.fetch_ohlcv', return_value=gcd.get_empty_ohlcv_df()):
            csv_result = csv_puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)
        stored_result = stored_puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)


        file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
        expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, csv_result)
        pd.testing.assert_frame_equal(stored_result, csv_result)

    def test_main_online_only(self):
        pass


if __name__ == "__main__":
    unittest.main()