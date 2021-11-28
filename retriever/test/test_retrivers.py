import unittest
import pandas as pd
from rba_tools.retriever.timeframe import Timeframe
from datetime import datetime
import os
import rba_tools.retriever.get_crypto_data as gcd
import rba_tools.retriever.retrievers as retrievers
import rba_tools.retriever.database_interface as dbi
from pathlib import Path

PERFORM_API_TESTS = True



class TestRetriever(unittest.TestCase):

     @classmethod
     def setUpClass(cls):
          """clear out test data if it exists"""
          db = dbi.SQLite3OHLCVDatabase(test=True)
          if os.path.exists(db.get_database_file()):
               os.remove(db.get_database_file())

     def test_CSVDataRetriever(self):
          csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
          retriever = retrievers.CSVDataRetriever(csv_file)
          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1D')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          expected = pd.read_csv(csv_file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(expected, result)
     
     def test_CCXTDataRetriever_Basic(self):
          """test a simple CCXT single data pull"""
          if not PERFORM_API_TESTS:
               return

          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1h')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 20)
          retriever = retrievers.CCXTDataRetriever('binance')
          result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
          expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(result, expected)

     def test_CCXTDataRetriever_Retriever_Multicall(self):
          """test a CCXT request that requres multiple API calls"""
          if not PERFORM_API_TESTS:
               return

          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1h')
          from_date = datetime(2021, 1, 1)
          to_date = datetime(2021, 1, 31)
          retriever = retrievers.CCXTDataRetriever('binance')
          result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          file = str(Path(__file__).parent) + '\ETH_BTC_1H_2021-1-1.csv'
          expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(result, expected)

     def test_Retreivers_Return_Equal(self):
          if not PERFORM_API_TESTS:
               return

          csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
          csv_retriever = retrievers.CSVDataRetriever(csv_file)
          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1d')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          csv_result = csv_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          ccxt_retriever = retrievers.CCXTDataRetriever('binance')
          ccxt_result = ccxt_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          pd.testing.assert_frame_equal(csv_result, ccxt_result)

          sqlite3_db = dbi.SQLite3OHLCVDatabase(True)
          sqlite3_db.store_dataframe(csv_result, timeframe)

          db_retriever = retrievers.DatabaseRetriever(sqlite3_db)
          db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          pd.testing.assert_frame_equal(db_retriever_result, ccxt_result)

if __name__ == "__main__":
    unittest.main()