import unittest
import pandas as pd
from rba_tools.retriver.timeframe import Timeframe
from datetime import datetime
import os
import rba_tools.retriver.get_crypto_data as gcd
from pathlib import Path

PERFORM_API_TESTS = True



class Testgcd(unittest.TestCase):

     @classmethod
     def setUpClass(cls):
          """clear out test data if it exists"""
          db = gcd.SQLite3OHLCVDatabase(test=True)
          if os.path.exists(db.get_database_file()):
               os.remove(db.get_database_file())

     def test_CSVDataRetriver(self):
          csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
          retriever = gcd.CSVDataRetriver(csv_file)
          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1D')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          expected = pd.read_csv(csv_file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(expected, result)
     
     def test_CCXTDataRetriver_Retriver_Basic(self):
          """test a simple CCXT single data pull"""
          if not PERFORM_API_TESTS:
               return

          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1h')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 20)
          retriver = gcd.CCXTDataRetriver('binance')
          result = retriver.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          file = str(Path(__file__).parent) + '\ETH_BTC_1H_2020-1-1.csv'
          expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(result, expected)

     def test_CCXTDataRetriver_Retriver_Multicall(self):
          """test a CCXT request that requres multiple API calls"""
          if not PERFORM_API_TESTS:
               return

          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1h')
          from_date = datetime(2021, 1, 1)
          to_date = datetime(2021, 1, 31)
          retriver = gcd.CCXTDataRetriver('binance')
          result = retriver.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          file = str(Path(__file__).parent) + '\ETH_BTC_1H_2021-1-1.csv'
          expected = pd.read_csv(file, parse_dates=True, index_col='Timestamp')

          pd.testing.assert_frame_equal(result, expected)

     def test_Retreivers_Return_Equal(self):
          if not PERFORM_API_TESTS:
               return

          csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
          csv_retriever = gcd.CSVDataRetriver(csv_file)
          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1d')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          csv_result = csv_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          ccxt_retriver = gcd.CCXTDataRetriver('binance')
          ccxt_result = ccxt_retriver.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          pd.testing.assert_frame_equal(csv_result, ccxt_result)



     def test_sqlite3_store_and_retrieve(self):
          csv_file = str(Path(__file__).parent) + '\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
          retriever = gcd.CSVDataRetriver(csv_file)
          symbol = 'ETH/BTC'
          timeframe = Timeframe.from_string('1D')
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          csv_result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          sqlite3_db = gcd.SQLite3OHLCVDatabase(True)

          sqlite3_db.store_dataframe(csv_result, timeframe)

          db_retriever = gcd.DatabaseRetriver(sqlite3_db)

          db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          pd.testing.assert_frame_equal(csv_result, db_retriever_result)

     def test_main(self):
          
          


if __name__ == "__main__":
    unittest.main()