from rba_tools.retriever.timeframe import Timeframe
import unittest
from datetime import timedelta

class TestTimeframe(unittest.TestCase):

    def test_init(self):
        expected = timedelta(seconds=60)
        result = Timeframe(expected).timeframe
        self.assertEqual(expected, result)

    def test_from_seconds(self):
        expected = timedelta(seconds=60)
        result = Timeframe.from_seconds(60).timeframe
        self.assertEqual(expected, result)


    def test_convert_timeframe_string_to_sec_minutes(self):
        result = Timeframe.convert_timeframe_string_to_sec('m')
        expected = 60
        self.assertEqual(result, expected)

        result = Timeframe.convert_timeframe_string_to_sec('5m')
        expected = 5 * 60
        self.assertEqual(result, expected)

        result = Timeframe.convert_timeframe_string_to_sec('180m')
        expected = 180 * 60
        self.assertEqual(result, expected)

    def test_convert_timeframe_string_to_sec_hours(self):
        result = Timeframe.convert_timeframe_string_to_sec('5h')
        expected = 60 * 60 * 5
        self.assertEqual(result, expected)

    def test_convert_timeframe_string_to_sec_days(self):
        result = Timeframe.convert_timeframe_string_to_sec('2d')
        expected = 60 * 60 * 24 * 2
        self.assertEqual(result, expected)


    def test_from_string(self):
        expected = timedelta(seconds=60)
        result = Timeframe.from_string('60s')
        self.assertEqual(expected, result.timeframe)

        expected = timedelta(seconds=300)
        result = Timeframe.from_string('5m')
        self.assertEqual(expected, result.timeframe)

    def test_get_timeframe_seconds(self):
        expected = 60
        result = Timeframe.from_seconds(expected).get_timeframe_seconds()
        self.assertEqual(expected, result)


    def test_get_timeframe_name_from_str(self):
        result = Timeframe.from_string('60s').get_timeframe_name()
        expected = '1M'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('m').get_timeframe_name()
        expected = '1M'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('300s').get_timeframe_name()
        expected = '5M'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('60m').get_timeframe_name()
        expected = '1H'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('4h').get_timeframe_name()
        expected = '4H'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('24h').get_timeframe_name()
        expected = '1D'
        self.assertEqual(result, expected)

        result = Timeframe.from_string('7d').get_timeframe_name()
        expected = '7D'
        self.assertEqual(result, expected)

    
    def test_get_timeframe_table_name(self):
        result = Timeframe.from_seconds(60).get_timeframe_table_name()
        expected = 'TIMEFRAME_1M'
        self.assertEqual(result, expected)


    def test_get_highest_time_increment_symbol(self):
        result = Timeframe.from_seconds(60).get_highest_time_increment_symbol()
        expected = 'M'
        self.assertEqual(result, expected)

        result = Timeframe.from_seconds(60*60*2).get_highest_time_increment_symbol()
        expected = 'H'
        self.assertEqual(result, expected)

        result = Timeframe.from_seconds(60*60*24).get_highest_time_increment_symbol()
        expected = 'D'
        self.assertEqual(result, expected)

        result = Timeframe.from_seconds(60*60*1.5).get_highest_time_increment_symbol()
        expected = 'M'
        self.assertEqual(result, expected)

    def test_eq(self):
        self.assertTrue(Timeframe.from_seconds(60) == Timeframe.from_seconds(60))

    


if __name__ == "__main__":
    unittest.main()