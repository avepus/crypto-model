import unittest
import rba_tools.backtest.backtrader_extensions.plotting.plot as rbsplot




class TestPlottingPlot(unittest.TestCase):


    def test_truncate_str_to_max_chars_30_chars(self):
        """test a simple csv retreiver data pull"""
        string = '123456789012345678901234567890'
        expected = '123456789012345678..'

        result = rbsplot.truncate_str_to_max_chars(string)

        self.assertEqual(expected, result)

    def test_truncate_str_to_max_chars_20_chars(self):
        """test a simple csv retreiver data pull"""
        string = '12345678901234567890'
        expected = string

        result = rbsplot.truncate_str_to_max_chars(string)

        self.assertEqual(expected, result)
    
    def test_truncate_str_to_max_chars_10_chars(self):
        """test a simple csv retreiver data pull"""
        string = '1234567890'
        expected = string

        result = rbsplot.truncate_str_to_max_chars(string)

        self.assertEqual(expected, result)
    
    


if __name__ == "__main__":
    unittest.main()