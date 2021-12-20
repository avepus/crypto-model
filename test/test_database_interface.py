import unittest
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
from datetime import datetime
import os
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
import rba_tools.retriever.get_crypto_data as gcd
from pathlib import Path

PERFORM_API_TESTS = True




class TestDatabaseInterface(unittest.TestCase):

    
    def setUp(self):
        """clear out test data if it exists"""
        db = dbi.SQLite3OHLCVDatabase(test=True)
        if os.path.exists(db.get_database_file()):
            os.remove(db.get_database_file())

    def test_sqlite3_blank_retrieval(self):
        symbol = 'ETH/BTC'
        timeframe = Timeframe.from_string('1D')
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2020, 12, 3)

        sqlite3_db = dbi.SQLite3OHLCVDatabase(True)

        db_retriever = retrievers.DatabaseRetriever(sqlite3_db)
        db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        expected = gcd.get_empty_ohlcv_df()

        pd.testing.assert_frame_equal(expected, db_retriever_result)

    def test_sqlite3_csv_store_and_retrieve(self):
        csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
        retriever = retrievers.CSVDataRetriever(csv_file)
        symbol = 'ETH/BTC'
        timeframe = Timeframe.from_string('1D')
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2020, 12, 3)
        csv_result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        sqlite3_db = dbi.SQLite3OHLCVDatabase(True)

        sqlite3_db.store_dataframe(csv_result, timeframe)

        #verify we have three rows in the table that was just created
        result = sqlite3_db._execute_query(f"SELECT COUNT(Symbol) FROM {timeframe.get_timeframe_table_name()}")
        self.assertEqual(3, int(result[0][0]))

        #verify retrieved data from database matches the CSV retrived data
        db_retriever = retrievers.DatabaseRetriever(sqlite3_db)
        db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        pd.testing.assert_frame_equal(csv_result, db_retriever_result)

if __name__ == "__main__":
    unittest.main()