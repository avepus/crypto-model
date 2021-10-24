import unittest
import rba_tools.utils as utils


class Testutils(unittest.TestCase):

    def test_convert_timeframe_to_sec_seconds(self):
        result = utils.convert_timeframe_to_sec('5s')
        expected = 5
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

    

    def test_timeframe_name(self):
        result = utils.timeframe_name('60s')
        expected = '1M'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('m')
        expected = '1M'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('300s')
        expected = '5M'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('60m')
        expected = '1H'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('4h')
        expected = '4H'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('24h')
        expected = '1D'
        self.assertEqual(result, expected)

        result = utils.timeframe_name('7d')
        expected = '7D'
        self.assertEqual(result, expected)

    def test_get_highest_time_increment(self):
        result = utils.get_highest_time_increment(60)
        expected = 'M'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment(60*60*2)
        expected = 'H'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment(60*60*24)
        expected = 'D'
        self.assertEqual(result, expected)

        result = utils.get_highest_time_increment(60*60*1.5)
        expected = 'M'
        self.assertEqual(result, expected)

    def test_timeframe_name_exception(self):
        self.assertRaises(ValueError, utils.timeframe_name, '30s')

        self.assertRaises(ValueError, utils.timeframe_name, '183s')
         

if __name__ == "__main__":
    unittest.main()