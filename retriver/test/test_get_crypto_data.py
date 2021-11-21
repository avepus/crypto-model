import unittest
import pandas as pd
#The lines below allow us to import from the parent directory in a hacky way. Technically https://stackoverflow.com/a/50194143 is the "most right" way to do this
import numpy as np
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
          timeframe = '1D'
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
          timeframe = '1h'
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
          timeframe = '1h'
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
          timeframe = '1d'
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
          timeframe = '1D'
          from_date = datetime(2020, 12, 1)
          to_date = datetime(2020, 12, 3)
          csv_result = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          sqlite3_db = gcd.SQLite3OHLCVDatabase(True)

          sqlite3_db.store_dataframe(csv_result)

          db_retriever = gcd.DatabaseRetriver(sqlite3_db)

          db_retriever_result = db_retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

          pd.testing.assert_frame_equal(csv_result, db_retriever_result)
          

     # def test_get_DataFrame(self):
     #      #verifies that retriving the data from online source and from saved file yield the same dataframe
     #      if os.path.exists(db_file):
     #           os.remove(db_file)
     #      binance = gcd.getBinanceExchange()
     #      eth_btc_data_from_exchange = gcd.get_DataFrame(['ETH/BTC'], binance, '8/1/18', '12/1/20')
     #      eth_btc_saved_data = gcd.get_DataFrame(['ETH/BTC'], binance, '8/1/18', '12/1/20')

     #      pd.testing.assert_frame_equal(eth_btc_data_from_exchange, eth_btc_saved_data)


     #      #verify that the data retrieved actually matches with a subset of that historic data.
     #      #Returning nothing matches nothing so this validates that we are actually returning data
     #      csv_file = str(Path(__file__).parent) + '\\eth_test_data.csv'
     #      expected_dataframe = pd.read_csv(csv_file, parse_dates=True, index_col='Timestamp')

     #      pd.testing.assert_frame_equal(eth_btc_saved_data, expected_dataframe)


     #      #verify that we will pull previous data if it's missing
     #      eth_btc_data_from_exchange = gcd.get_DataFrame(['ETH/BTC'], binance, '7/29/18', '12/1/20')

     #      append_data = [[0.056990,0.057097,0.056554,0.056777,83117.255,'ETH/BTC',np.nan],
     #                     [0.056794,0.057074,0.055500,0.055866,102153.439,'ETH/BTC',np.nan],
     #                     [0.055862,0.056316,0.054356,0.055815,118270.566,'ETH/BTC',np.nan]]
     #      append_index = pd.to_datetime(['7/29/18','7/30/18','7/31/18'])
     #      append_df = pd.DataFrame(data=append_data, index=append_index, columns=eth_btc_data_from_exchange.columns)
     #      append_df.index.name = 'Timestamp'
     #      eth_btc_saved_data = eth_btc_saved_data.append(append_df).sort_index()
     #      pd.testing.assert_frame_equal(eth_btc_data_from_exchange, eth_btc_saved_data)

          

     #      #verify that if we have the newest historical data possible and we request newer data, we won't attempt to pull more data
     #      binance_pull_df = gcd.get_DataFrame(['AE/BTC'], binance, '12/25/20', '1/1/21')
     #      print('Test 4. No data retrievals should occur between here')
     #      saved_data_df = gcd.get_DataFrame(['AE/BTC'], binance, '12/25/20', '1/20/21')
     #      print('and here.')
     #      pd.testing.assert_frame_equal(binance_pull_df, saved_data_df)


     #      #verify that if we have the oldest historical data possible and we request older data, we won't attempt to pull more data
     #      binance_pull_df = gcd.get_DataFrame(['RIF/BTC'], binance, '1/1/21', '1/20/21')
     #      print('Test 3. No data retrievals should occur between here')
     #      saved_data_df = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/20/21')
     #      print('and here.')
     #      pd.testing.assert_frame_equal(binance_pull_df, saved_data_df)

     #      #verify that we will pull future data if it's missing
     #      new_data_pull = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/23/21') #left off here we set is_final_column incorrectly

     #      append_data = [[0.00000511,0.00000545,0.00000504,0.00000515,1249678.0,'RIF/BTC',np.nan],
     #                     [0.00000515,0.00000527,0.00000492,0.00000501,1708724.0,'RIF/BTC',np.nan],
     #                     [0.00000503,0.00000545,0.00000499,0.00000521,1852288.0,'RIF/BTC',np.nan]]
     #      append_index = pd.to_datetime(['1/21/21','1/22/21','1/23/21'])
     #      append_df = pd.DataFrame(data=append_data, index=append_index, columns=saved_data_df.columns)
     #      append_df.index.name = 'Timestamp'
          
     #      expected_data = saved_data_df.append(append_df).sort_index()
     #      pd.testing.assert_frame_equal(new_data_pull, expected_data)

     #      #verify that data was not duplicated in our database when we did our previous step
     #      #note this test must be performe after the step that verifies we will pull future data if it's missing
     #      saved_data_df = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/23/21')
     #      pd.testing.assert_frame_equal(new_data_pull, new_data_pull)

     #      #verify that we correctly pull prior data and new data at the same time
     #      eth_btc_data_from_exchange = gcd.get_DataFrame(['ETH/BTC'], binance, '7/27/18', '12/3/20')
          
     #      append_data = [[0.058309,0.058950,0.056703,0.057446,98918.122,'ETH/BTC',np.nan],
     #                     [0.057447,0.057519,0.056686,0.056937,80417.052,'ETH/BTC',np.nan],
     #                     [0.031189,0.031621,0.030974,0.031091,239428.833,'ETH/BTC',np.nan],
     #                     [0.031091,0.031826,0.030961,0.031709,310741.578,'ETH/BTC',np.nan]]
     #      append_index = pd.to_datetime(['7/27/18','7/28/18','12/2/20','12/3/20'])
     #      append_df = pd.DataFrame(data=append_data, index=append_index, columns=saved_data_df.columns)
     #      append_df.index.name = 'Timestamp'

     #      eth_btc_saved_data = eth_btc_saved_data.append(append_df).sort_index()
     #      pd.testing.assert_frame_equal(eth_btc_data_from_exchange, eth_btc_saved_data)

     #      #need timeframe based test cases 
     #      #data is present but timeframe is not specific enough
     #      data_from_get = gcd.get_DataFrame(['ETH/BTC'], binance, '12/1/20', '12/3/20', timeframe='4h')
     #      expected_data = pd.read_csv(r'C:\Users\Avery\Documents\GitHub\rba_tools_project\rba_tools\test\ETH_BTC_4h_12-1-20_to_12-3-20.csv'
     #                                  ,index_col = 'Timestamp'
     #                                  ,parse_dates = True)
     #      pd.testing.assert_frame_equal(data_from_get, expected_data)

     #      #data is present and more specific data is available but not pulled when higher timeframe is requested
     #      data_from_get = gcd.get_DataFrame(['ETH/BTC'], binance, '12/1/20', '12/3/20', timeframe='1d')
     #      expected_data = pd.read_csv(r'C:\Users\Avery\Documents\GitHub\rba_tools_project\rba_tools\test\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
     #                                  ,index_col = 'Timestamp'
     #                                  ,parse_dates = True)
     #      print('data_from_get')
     #      print(data_from_get)
     #      print('expected_data')
     #      print(expected_data)
     #      pd.testing.assert_frame_equal(data_from_get, expected_data)

     #      #testing pulling 1H and pulling up to saved data
     #      expected_data = pd.read_csv(r'C:\Users\Avery\Documents\GitHub\rba_tools_project\rba_tools\test\ETH_BTC_1H_11-30-20_to-12-1-20.csv'
     #                                  ,index_col = 'Timestamp'
     #                                  ,parse_dates = True)
     #      pd.testing.assert_frame_equal(data_from_get, expected_data)

if __name__ == "__main__":
    unittest.main()