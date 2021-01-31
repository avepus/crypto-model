import unittest
import pandas as pd
#The lines below allow us to import from the parent directory in a hacky way. Technically https://stackoverflow.com/a/50194143 is the "most right" way to do this
import os,sys,inspect
import numpy as np
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(1,parentdir) 

import get_crypto_data as gcd
import database
database.database_file = 'test\\test_ohlcv_sqlite.db'

class Testgcd(unittest.TestCase):



     def test_get_DataFrame(self):
          #test 1
          #verifies that retriving the data from online source and from saved file yield the same dataframe
          if os.path.exists('test\\test_ohlcv_sqlite.db'):
               os.remove('test\\test_ohlcv_sqlite.db')
          binance = gcd.getBinanceExchange()
          binance_pull_df = gcd.get_DataFrame(['ETH/BTC'], binance, '8/1/18', '12/1/20')
          saved_data_df = gcd.get_DataFrame(['ETH/BTC'], binance, '8/1/18', '12/1/20')

          pd.testing.assert_frame_equal(binance_pull_df, saved_data_df)

          #verify that the data retrieved actually matches with a subset of that historic data.
          #Returning nothing matches nothing so this validates that we are actually returning data
          eth_btc_data = [[1533081600000,0.055818,0.056429,0.054463,0.05525,106706.644,'ETH/BTC',np.nan],
                          [1533168000000,0.05525,0.055589,0.054143,0.05455,102662.715,'ETH/BTC',np.nan],
                          [1533254400000,0.05455,0.056501,0.0542,0.056334,125645.875,'ETH/BTC',np.nan]]
          eth_aug_1st_2nd_3rd = pd.DataFrame(eth_btc_data,
                                 columns=['Timestamp','Open','High','Low','Close','Volume','Symbol','Is_Final_Row'])
          

          eth_aug_1st_2nd_3rd = gcd.set_data_timestamp_index(eth_aug_1st_2nd_3rd)
          saved_eth_aug_1st_2nd_3rd = gcd.get_DataFrame(['ETH/BTC'], binance, '8/1/18', '8/3/18')

          pd.testing.assert_frame_equal(eth_aug_1st_2nd_3rd, saved_eth_aug_1st_2nd_3rd)


          

          #verify that if we have the newest historical data possible and we request newer data, we won't attempt to pull more data
          binance_pull_df = gcd.get_DataFrame(['AE/BTC'], binance, '12/25/20', '1/1/21')
          print('Test 4. No data retrievals should occur between here')
          saved_data_df = gcd.get_DataFrame(['AE/BTC'], binance, '12/25/20', '1/20/21')
          print('and here.')
          pd.testing.assert_frame_equal(binance_pull_df, saved_data_df)

          #verify that we will pull previous data if it's missing

          #verify that if we have the oldest historical data possible and we request older data, we won't attempt to pull more data
          binance_pull_df = gcd.get_DataFrame(['RIF/BTC'], binance, '1/1/21', '1/20/21')
          print('Test 3. No data retrievals should occur between here')
          saved_data_df = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/20/21')
          print('and here.')
          pd.testing.assert_frame_equal(binance_pull_df, saved_data_df)

          #verify that we will pull future data if it's missing
          new_data_pull = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/23/21') #left off here we set is_final_column incorrectly

          append_data = [[0.00000511,0.00000545,0.00000504,0.00000515,1249678.0,'RIF/BTC',np.nan],
                         [0.00000515,0.00000527,0.00000492,0.00000501,1708724.0,'RIF/BTC',np.nan],
                         [0.00000503,0.00000545,0.00000499,0.00000521,1852288.0,'RIF/BTC',np.nan]]
          append_index = [1611187200000,1611273600000,1611360000000]
          append_df = pd.DataFrame(data=append_data, index=append_index, columns=saved_data_df.columns)
          append_df.index = pd.to_datetime(append_df.index, unit='ms')
          append_df.index.name = 'Timestamp'
          
          expected_data = saved_data_df.append(append_df)
          pd.testing.assert_frame_equal(new_data_pull, expected_data)

          #verify that data was not duplicated in our database when we did our previous step
          #note this test must be performe after the step that verifies we will pull future data if it's missing
          saved_data_df = gcd.get_DataFrame(['RIF/BTC'], binance, '12/1/20', '1/23/21')
          pd.testing.assert_frame_equal(new_data_pull, new_data_pull)


          #verify that we won't pull new data if the most recent data in our current data is less than two days old



    
    
     #def test_clean_columns(self):
     #    self.assertEqual(len(expected),len(result), message)


if __name__ == "__main__":
    unittest.main()