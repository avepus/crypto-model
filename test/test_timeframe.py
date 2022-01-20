# -*- coding: utf-8 -*-
"""Tests for timeframe

Created on Sat Nov 01 2021

@author: Avery

"""
import unittest
from datetime import timedelta
from rba_tools.retriever.timeframe import Timeframe

class TestTimeframe(unittest.TestCase):
    """class for testing Timeframe"""

    def test_init(self):
        """test creating Timeframe object"""
        expected = timedelta(seconds=60)
        result = Timeframe(expected).timeframe
        self.assertEqual(expected, result)

    def test_from_seconds(self):
        """test creating Timeframe object from number of seconds"""
        expected = timedelta(seconds=60)
        result = Timeframe.from_seconds(60).timeframe
        self.assertEqual(expected, result)

    def test_from_string(self):
        """test creating Timeframe object from string"""
        expected = timedelta(seconds=60)
        result = Timeframe.from_string('60s')
        self.assertEqual(expected, result.timeframe)

        expected = timedelta(seconds=300)
        result = Timeframe.from_string('5m')
        self.assertEqual(expected, result.timeframe)


    def test_convert_timeframe_string_to_sec_minutes(self):
        """test function that converts string to seconds using minutes"""
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
        """test function that converts string to seconds using hours"""
        result = Timeframe.convert_timeframe_string_to_sec('5h')
        expected = 60 * 60 * 5
        self.assertEqual(result, expected)

    def test_convert_timeframe_string_to_sec_days(self):
        """test function that converts string to seconds using days"""
        result = Timeframe.convert_timeframe_string_to_sec('2d')
        expected = 60 * 60 * 24 * 2
        self.assertEqual(result, expected)


    def test_get_timeframe_seconds(self):
        """test function that retrieves number of seconds in timeframe"""
        expected = 60
        result = Timeframe.from_seconds(expected).get_timeframe_seconds()
        self.assertEqual(expected, result)


    def test__str__(self):
        """test function that gets the name of the timeframe as a string"""
        result = str(Timeframe.from_string('60s'))
        expected = '1M'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('m'))
        expected = '1M'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('300s'))
        expected = '5M'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('60m'))
        expected = '1H'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('4h'))
        expected = '4H'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('24h'))
        expected = '1D'
        self.assertEqual(result, expected)

        result = str(Timeframe.from_string('7d'))
        expected = '7D'
        self.assertEqual(result, expected)


    def test_get_timeframe_table_name(self):
        """test function that gets database table name"""
        result = Timeframe.from_seconds(60).get_timeframe_table_name()
        expected = 'TIMEFRAME_1M'
        self.assertEqual(result, expected)


    def test_get_highest_time_increment_symbol(self):
        """test function that gets the highest timeframe divisible increment.
        E.g. for 180 seconds the highest divisible timeframe increment is minutes"""
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
        """test equals operator"""
        self.assertTrue(Timeframe.from_seconds(60) == Timeframe.from_seconds(60))



if __name__ == "__main__":
    unittest.main()
