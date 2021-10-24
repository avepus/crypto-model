import unittest
import rba_tools.utils as utils


class Testgcd(unittest.TestCase):

    def seconds_test_convert_timeframe_to_sec(self):
        result = utils.convert_timeframe_to_sec('5s')
        expected = 5
        self.assertEqual(result, expected)

    def minutes_1_test_convert_timeframe_to_sec(self):
        result = utils.convert_timeframe_to_sec('5m')
        expected = 5 * 60
        self.assertEqual(result, expected)

        result = utils.convert_timeframe_to_sec('180m')
        expected = 5 * 60
        self.assertEqual(result, expected)

        result = utils.convert_timeframe_to_sec('m')
        expected = 60
        self.assertEqual
        (result, expected)


    def hours_test_convert_timeframe_to_sec(self):
        result = utils.convert_timeframe_to_sec('5h')
        expected = 5 * 60 * 60
        self.assertEqual(result, expected)

    def days_test_convert_timeframe_to_sec(self):
        result = utils.convert_timeframe_to_sec('2d')
        expected = 5 * 60 * 60 * 24 * 2
        self.assertEqual(result, expected)

    

    def test_timeframe_name(self):
        result = utils.timeframe_name('60m')
        expected = '1H'
        self.assertEqual(result, expected)
         

if __name__ == "__main__":
    unittest.main()