# -*- coding: utf-8 -*-
"""Tests for database_interface

Created on Sat Nov 01 2021

@author: Avery

"""
import os
import unittest
from datetime import datetime
from pathlib import Path
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
from rba_tools.retriever.constants import empty_ohlcv_df_generator

PERFORM_API_TESTS = True




class TestDatabaseInterface(unittest.TestCase):
    """class for testing DatabaseInterface"""

    def setUp(self):
        """clear out test data if it exists"""
        database = dbi.SQLite3OHLCVDatabase(test=True)
        if os.path.exists(database.get_database_file()):
            os.remove(database.get_database_file())

    def test_sqlite3_blank_retrieval(self):
        """verify retrieving from blank database returns empty df"""
        symbol = 'ETH/BTC'
        timeframe = Timeframe.from_string('1D')
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2020, 12, 3)

        sqlite3_db = dbi.SQLite3OHLCVDatabase(True)

        db_retriever = retrievers.DatabaseRetriever(sqlite3_db)
        db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        expected = empty_ohlcv_df_generator()

        pd.testing.assert_frame_equal(expected, db_retriever_result)

    def test_sqlite3_csv_store_and_retrieve(self):
        """verify retriving from stored sqlite3 database matches csv result"""
        csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
        retriever = retrievers.CSVDataRetriever(csv_file)
        symbol = 'ETH/BTC'
        timeframe = Timeframe.from_string('1D')
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2020, 12, 3)
        csv_result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        sqlite3_db = dbi.SQLite3OHLCVDatabase(True)

        sqlite3_db.store_dataframe(csv_result, timeframe)

        #verify retrieved data from database matches the CSV retrived data
        db_retriever = retrievers.DatabaseRetriever(sqlite3_db)
        db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        pd.testing.assert_frame_equal(csv_result, db_retriever_result)

if __name__ == "__main__":
    unittest.main()
