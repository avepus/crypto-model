import unittest
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
from datetime import datetime
import os
import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
from dateutil import parser
from pathlib import Path

PERFORM_API_TESTS = True



class TestMain(unittest.TestCase):

    def setUp(self):
        """clear out test data if it exists"""
        db = dbi.SQLite3OHLCVDatabase(test=True)
        if os.path.exists(db.get_database_file()):
            os.remove(db.get_database_file())
    
    def test_main_online_then_stored(self):
        """calls main method with some defaults"""
        database = dbi.SQLite3OHLCVDatabase(test=True)
        stored_retriever = retrievers.DatabaseRetriever(database)
        online_retriever = retrievers.CCXTDataRetriever('binance')
        puller = gcd.DataPuller(stored_retriever, online_retriever, database)

        symbol = 'ETH/BTC'
        timeframe_str = '1h'
        from_date_str = '12-1-2020'
        to_date_str = '12-20-2020'

        result = puller.fetch_df(symbol, timeframe_str, from_date_str, to_date_str)

        file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
        expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

        pd.testing.assert_frame_equal(expected, result)

    

    

    def test_main_stored_only(self):
        pass

    def test_main_online_only(self):
        pass


if __name__ == "__main__":
    unittest.main()