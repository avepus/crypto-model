import unittest
import rba_tools.utils as utils
from pandas import DataFrame
import rba_tools.retriever.get_crypto_data as gcd
from pathlib import Path
from datetime import datetime


class Testutils(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        csv_file = str(Path(__file__).parent.parent.parent) + '\\retriver\\test\\ETH_BTC_1D_12-1-20_to-12-3-20.csv'
        retriever = gcd.CSVDataRetriver(csv_file)
        symbol = 'ETH/BTC'
        timeframe = '1D'
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2020, 12, 3)
        cls.df_1d = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)

        csv_file = str(Path(__file__).parent.parent.parent) + '\\retriver\\test\\ETH_BTC_1H_2020-1-1.csv'
        retriever = gcd.CSVDataRetriver(csv_file)
        symbol = 'ETH/BTC'
        timeframe = '1h'
        from_date = datetime(2020, 12, 1)
        to_date = datetime(2021, 12, 3)
        cls.df_1h = retriever.fetch_ohlcv(symbol, timeframe, from_date, to_date)



    def test_convert_timeframe_to_sec_seconds(self):
        result = utils.convert_timeframe_to_sec('5s')
        expected = 5
        self.assertEqual(result, expected)

    def test_get_timeframe_name_from_seconds(self):
        result = utils.get_timeframe_name_from_seconds(60)
        expected = '1M'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_seconds(120)
        expected = '2M'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_seconds(7200)
        expected = '2H'
        self.assertEqual(result, expected)

    def test_convert_timeframe_to_sec_minutes(self):
        result = utils.convert_timeframe_to_sec('m')
        expected = 60
        self.assertEqual(result, expected)

        result = utils.convert_timeframe_to_sec('5m')
        expected = 5 * 60
        self.assertEqual(result, expected)

        result = utils.convert_timeframe_to_sec('180m')
        expected = 180 * 60
        self.assertEqual(result, expected)

    def test_convert_timeframe_to_sec_hours(self):
        result = utils.convert_timeframe_to_sec('5h')
        expected = 60 * 60 * 5
        self.assertEqual(result, expected)

    def test_convert_timeframe_to_sec_days(self):
        result = utils.convert_timeframe_to_sec('2d')
        expected = 60 * 60 * 24 * 2
        self.assertEqual(result, expected)


    def test_get_timeframe_name_from_str(self):
        result = utils.get_timeframe_name_from_str('60s')
        expected = '1M'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('m')
        expected = '1M'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('300s')
        expected = '5M'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('60m')
        expected = '1H'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('4h')
        expected = '4H'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('24h')
        expected = '1D'
        self.assertEqual(result, expected)

        result = utils.get_timeframe_name_from_str('7d')
        expected = '7D'
        self.assertEqual(result, expected)

    def test_timeframe_name_exception(self):
        self.assertRaises(ValueError, utils.get_timeframe_name_from_str, '30s')

        self.assertRaises(ValueError, utils.get_timeframe_name_from_str, '183s')

    def test_get_highest_time_increment_symbol(self):
        result = utils.get_highest_time_increment_symbol(60)
        expected = 'M'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment_symbol(60*60*2)
        expected = 'H'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment_symbol(60*60*24)
        expected = 'D'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment_symbol(60*60*1.5)
        expected = 'M'
        self.assertEqual(result, expected)
        

    def test_get_seconds_timeframe_from_df(self):
        result = utils.get_timeframe_in_seconds_from_df(self.df_1d)
        expected = 24*60*60
        self.assertEqual(result, expected)

        result = utils.get_timeframe_in_seconds_from_df(self.df_1h)
        expected = 60*60
        self.assertEqual(result, expected)

    
         

if __name__ == "__main__":
    unittest.main()