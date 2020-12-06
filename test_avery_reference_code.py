# -*- coding: utf-8 -*-
"""
Created on Fri Apr 10 22:06:48 2020

@author: Avery
"""

import unittest
import as_Class as aml
import pandas as pd
import numpy as np
import getCryptoData as gcd
import os.path as path

class Testaml(unittest.TestCase):
    
    
    
    def test_count_tickers(self):
        #test two tickers
        d = {("Adj Close","CHK"): [1, 2],
             ("Adj Close","T"): [3, 4],
             ("Close","CHK"): [2, 3],
             ("Close", "T"): [5, 1]}
        df = pd.DataFrame(data=d)
        self.assertEqual(aml.count_tickers(df), 2)
        
        #test three tickers
        d = {("Adj Close","CHK"): [1, 2],
             ("Adj Close","T"): [3, 4],
             ("Adj Close","AAPL"): [3, 4],
             ("Close","CHK"): [2, 3],
             ("Close", "T"): [5, 1],
             ("Close","AAPL"): [9, 4]}
        df = pd.DataFrame(data=d)
        self.assertEqual(aml.count_tickers(df), 3)
        
        #test one ticker
        d = {"Adj Close": [1, 2],
             "Close": [2, 3]}
        df = pd.DataFrame(data=d)
        self.assertEqual(aml.count_tickers(df), 1)
    
    
    def test_clean_columns(self):
        d = {("Adj Close","CHK"): [1.6, 2.45, 7.0],
             ("Adj Close","T"): [3, 4, 9.9],
             ("Adj Close","AAPL"): [8, 5.4, 0.1],
             ("Close","CHK"): [2.1, 3, 1],
             ("Close", "T"): [5, 1.5, 5.6],
             ("Close", "AAPL"): [5.6, 1, 5.1]}
        
        result = aml.clean_columns(pd.DataFrame(data=d))
        
        exp0 = {"Adj Close": [1.6, 2.45, 7.0],
                "Close": [2.1, 3, 1],
                "Ticker": ["CHK", "CHK", "CHK"]}
        exp1 = {"Adj Close": [3, 4, 9.9],
                "Close": [5, 1.5, 5.6],
                "Ticker": ["T", "T", "T"]}
        exp2 = {"Adj Close": [8, 5.4, 0.1],
                "Close": [5.6, 1, 5.1],
                "Ticker": ["AAPL", "AAPL", "AAPL"]}
        
        expected = [pd.DataFrame(data=exp0),
                    pd.DataFrame(data=exp1),
                    pd.DataFrame(data=exp2)]
        
        #check that lengths are equal
        message = "expected list length != result list length"
        self.assertEqual(len(expected),len(result), message)
        
        #check that each individual dataframe is equal
        for i in range(len(result)):
            message = "result[" + str(i) + "] != expected[" + str(i) + "]"
            self.assertTrue(result[i].equals(expected[i]), message)
        
        
        self.assertRaises(KeyError, aml.clean_columns, result[0])
        #maybe not needed?
        self.assertRaises(AttributeError, aml.clean_columns, "string")
        self.assertRaises(AttributeError, aml.clean_columns, 3)
    
    def test_movingAverageNP(self):
        d = np.array([1, 2, 3, -5, 0, 0, -100, 12.0])
        result = aml.movingAverageNP(d, 2)
        expected = np.array([np.nan, 1.5, 2.5, -1, -2.5, 0, -50, -44])
        np.testing.assert_array_equal(result, expected)
        
        result = aml.movingAverageNP(d, 4)
        expected = np.array([np.nan, np.nan, np.nan, 0.25, 0, -0.5, -26.25, -22])
        np.testing.assert_array_equal(result, expected)
    
    #def test_movingAveragePD
    #This is a one line call to pandas functions so it's not tested here
    
    #def test_emaNP(self):
    #I don't think I need a numpy EMA
    
    #def test_emaPD
    #This is a one line call to pandas functions so it's not tested here
    
    def test_calcSlope(self):
        d = pd.Series(data=[5, 1.5, 5.6])
        result = aml.calcSlope(d)
        expected = np.array([0, -3.5, 4.1])
        np.testing.assert_array_equal(result, expected)
    
    #def test_addMovingAverage
    #not tested due to simplicity
    
    def test_calc_Stochastic_K(self):
        #using data verified through tradingview
        d = {"Close": [6.41,6.51,6.53,7.22,7.21,7.49,7.76,8.10],
             "High": [6.53,6.58,6.57,7.27,7.77,7.62,7.89,8.14],
             "Low": [6.00,6.32,6.27,6.82,7.00,7.09,7.47,7.50]}
        d = pd.DataFrame(data = d)
        
        result = aml.calc_Stochastic_K(d, 4)
        expected = pd.Series([np.nan, np.nan, np.nan, 0.960630, 
                              0.626667,0.813333,0.878505,0.964912])
        result = np.round(result,3)
        expected = np.round(expected,3)
        np.testing.assert_array_equal(result, expected)
    
    #def test_addStochastic
    #not tested since it is built from other functions
    
    #def test_calc_MACD
    #not tested since it is built from other functions
    
    #def test_addMACD
    #not yet implemented
    
    #def test_addLongSuccess
    
    #def test_changeColumnToDate
    
    def test_clearDataLessThan(self):
        d = {"Close":[6.41, 6.51, 6.53, 7.22, 7.21, 7.49, 7.76, 8.10],
             "Date": [np.datetime64('2019-12-29')
                     ,np.datetime64('2019-12-30')
                     ,np.datetime64('2019-12-31')
                     ,np.datetime64('2020-01-01')
                     ,np.datetime64('2020-01-02')
                     ,np.datetime64('2020-01-03')
                     ,np.datetime64('2020-01-04')
                     ,np.datetime64('2020-01-05')]}
        df = pd.DataFrame(data = d)
        result = aml.clearDataLessThan(df, np.datetime64("2020-01-01"))
        
        expected = {"Close":[7.22, 7.21, 7.49, 7.76, 8.10],
                    "Date": [np.datetime64('2020-01-01')
                            ,np.datetime64('2020-01-02')
                            ,np.datetime64('2020-01-03')
                            ,np.datetime64('2020-01-04')
                            ,np.datetime64('2020-01-05')]}
        expected = pd.DataFrame(data = expected)
        
        pd.testing.assert_frame_equal(expected,result)
        
        result = aml.clearDataLessThan(df, 7.22, col="Close")
        
        expected = {"Close":[7.22, 7.49, 7.76, 8.10],
                    "Date": [np.datetime64('2020-01-01')
                            ,np.datetime64('2020-01-03')
                            ,np.datetime64('2020-01-04')
                            ,np.datetime64('2020-01-05')]}
        
        expected = pd.DataFrame(data = expected)
        
        pd.testing.assert_frame_equal(expected,result)
        
        
        
    
    #def test_addPercentageChange
    #not tested since it is built from basic pandas functions
    
    #def test_percentageOfColumn
    #not tested since it is built from basic pandas functions
    
    def test_consecutiveBarCount(self):
        d = {"Close": [2, 2.6, 2.8, 2.5, 2.1, 3, 3.5, 3, 2.75, 2.5],
              "Open": [1, 2.2, 2.6, 2.8, 2.5, 2, 3.9, 4, 2.85, 2.7]}
        d = pd.DataFrame(data = d)
        result = aml.consecutiveBarCount(d)
        expected = pd.Series([0, 0, 1, 0, -1, 0, 0, -1, -2, -3])
        
        np.testing.assert_array_equal(result, expected)
        
        #not needed. Should delete i think
    # def test_evaluateTrade(self):
    #     d = {"High": [2, 2.6, 2.8, 2.8, 2.5, 3, 3.9, 4, 2.85, 2.9],
    #           "Low": [1, 2.2, 2.6, 2.5, 2.1, 2, 3.5, 3, 2.75, 2.5],
    #           "Open": [1.5, 2.3, 2.6, 2.55, 2.5, 3, 3.6, 3.2, 2.75, 2.5]}
    #     d = pd.DataFrame(data = d)
        
    #     result = aml.evaluateTrade(d, 1, 2.4, 2.5, 2.0)
    #     result = np.round(result,3)
    #     self.assertEqual(result, 0.1)
        
        
    #     #test when hitting target takes a couple bars
    #     result = aml.evaluateTrade(d, 1, 2.59, 3, 1.99)
    #     result = np.round(result, 3)
    #     self.assertEqual(result, 0.41)
        
    #     #test when hitting stop loss takes a couple bars
    #     result = aml.evaluateTrade(d, 3, 2.7, 4.5, 2)
    #     result = np.round(result, 3)
    #     self.assertEqual(result, -0.7)
        
    #     #test corner case when day gaps above entry price
    #     #shouldn't happen with crypto but still handling it in case stock
    #     result = aml.evaluateTrade(d, 1, 2.1, 3, 1.9)
    #     np.testing.assert_equal(result, np.nan)
        
    #     #test corner case when entry price not hit
    #     result = aml.evaluateTrade(d, 0, 2.1, 2.6, 0.5)
    #     np.testing.assert_equal(result, np.nan)
        
    #     #test corner case when target and stoploss hit on same bar
    #     result = aml.evaluateTrade(d, 4, 2.2, 2.4, 2.1)
    #     np.testing.assert_equal(result, np.nan)
        
    #     #test corner case when target/stop loss is never hit
    #     result = aml.evaluateTrade(d, 8, 2.8, 3, 2.1)
    #     np.testing.assert_equal(result, np.nan)
        
    
    #test Class functions
        


    
    #["Open", "High", "Low", "Close", "Volume"]
    d = {"High": [2, 2.6, 2.8, 2.8, 2.5, 3, 3.9, 4, 2.85, 2.9],
         "Low": [1, 2.2, 2.6, 2.5, 2.1, 2, 3.5, 3, 2.75, 2.5],
         "Open": [1.5, 2.3, 2.6, 2.55, 2.5, 3, 3.6, 3.2, 2.75, 2.5],
         "Close": [1.4, 2.6, 2.6, 2.4, 2.2, 2, 3.7, 4, 2.8, 2.8],
         "Volume": [100, 110, 90, 150, 160, 155, 75, 90, 105, 110]}
    test_data = pd.DataFrame(data=d, index=pd.to_datetime(\
        ['1/1/20','1/2/20','1/3/20','1/4/20','1/5/20','1/6/20',
         '1/7/20','1/8/20','1/9/20','1/10/20']))
    test_data['Symbol'] = 'ETH/BTC'
    # Date	    High	Low	    Open    Close	Volume
    # 1/1/2020	2.00	1.00	1.50	1.40	100
    # 1/2/2020	2.60	2.20	2.30	2.60	110
    # 1/3/2020	2.80	2.60	2.60	2.60	90
    # 1/4/2020	2.80	2.50	2.55	2.40	150
    # 1/5/2020	2.50	2.10	2.50	2.20	160
    # 1/6/2020	3.00	2.00	3.00	2.00	155
    # 1/7/2020	3.90	3.50	3.60	3.70	75
    # 1/8/2020	4.00	3.00	3.20	4.00	90
    # 1/9/2020	2.85	2.75	2.75	2.80	105
    # 1/10/2020	2.90	2.50	2.50	2.80	110
    
    test_data.index.set_names("Date", inplace=True)
    test_data.to_csv("test_as_Class_test_data.csv")
    test_class = aml.DataSet(data = test_data)
    test_read_class = aml.DataSet(dataFile = "test_as_Class_test_data.csv")
    
    def test_init(self):
        pd.testing.assert_frame_equal(self.test_class.data, self.test_data)
        pd.testing.assert_frame_equal(self.test_read_class.data, self.test_data)
        
        #test timestamp column as index
        d = {"High": [2, 2.6, 3],
             "Low": [1, 2.2, 2],
             "Open": [1.5, 2.5, 2.5],
             "Close": [1.4, 2.6, 2.6],
             "Volume": [100, 110, 100],
             "Timestamp" : [1544745600000, 1544832000000, 1544918400000]}
        init_data = pd.DataFrame(data=d)
        init_data['Symbol'] = 'ETH/BTC'
        init_data.to_csv("test_as_Class_timestamp.csv", index=False)
        init_class = aml.DataSet(dataFile = "test_as_Class_timestamp.csv")
        expected = pd.DataFrame(data=d, index=pd.to_datetime(\
            ['12-14-2018', '12-15-2018', '12-16-2018']))
        expected['Symbol'] = 'ETH/BTC'
        expected.index.set_names("Timestamp", inplace=True)
        expected.drop("Timestamp", axis=1, inplace=True)
        #left off here
        pd.testing.assert_frame_equal(init_class.data, expected)
    
    def test_trailing_stop(self):
        result = self.test_class.trailing_stop('1/3/20')
        expected = 2.19
        self.assertEqual(result, expected)
        
        result = self.test_class.trailing_stop('1/6/20', 4)
        expected = 2.09
        self.assertEqual(result, expected)
        
        #corner case check when bars back goes outside of range
        #this raises an error. I don't think we should ever be getting the
        #stop loss at the edge like this but it might be worth handling better
        self.assertRaises(ValueError, self.test_class.trailing_stop, '1/1/20', 4)
    
    def test_evaluateTrade(self):
        #hit target
        testDate = pd.Timestamp('1/3/20')
        result = self.test_class.evaluateTrade(testDate, 2.7, 2.91, 0.9, False)
        expected = (pd.Timestamp('2020-01-06'), 0.21)
        self.assertEqual(result,expected)
        
        #hit stop-loss for loss
        testDate = pd.Timestamp('1/3/20')
        result = self.test_class.evaluateTrade(testDate, 2.7, stopLoss=2.49, stopLossFun=False)
        expected = (pd.Timestamp('2020-01-05'), -0.21)
        self.assertEqual(result, expected)
        
        #opened below stop-loss for bigger loss
        testDate = pd.Timestamp('1/2/20')
        result = self.test_class.evaluateTrade(testDate, 2.79, 3, 1)
        expected = (pd.Timestamp('2020-01-04'), -0.24)
        self.assertEqual(result, expected)
        
        #hit stop-loss for gain
        testDate = pd.Timestamp('1/1/20')
        result = self.test_class.evaluateTrade(testDate, 2.31)
        expected = (pd.Timestamp('2020-01-04'), 0.24)
        self.assertEqual(result, expected)
        
        #corner case trade not entered because under open
        testDate = pd.Timestamp('1/1/20')
        result = self.test_class.evaluateTrade(testDate, 2.29)
        expected = (pd.Timestamp('2020-01-01'), np.nan)
        self.assertEqual(result, expected)
    
    def test_get_tick(self):
        #test_class case
        result = self.test_class.get_tick()
        expected = 0.01
        self.assertEqual(result, expected)
        
        #test case with different decimal places and verify volume not counted
        d = {"High": [2, 2.0081],
             "Low": [1, 2.2],
             "Open": [1.5, 2.3],
             "Close": [1.4, 2.6],
             "Volume": [100.111111, 110],
             "Date" : ['1/1/20','1/2/20']}
        df = pd.DataFrame(data = d)
        df['Symbol'] = 'ETH/BTC'
        
        tick_class = aml.DataSet(data = df)
        result = tick_class.get_tick()
        expected = 0.0001
        self.assertEqual(result, expected)
        
        #test no decimals
        d = {"High": [11, 15],
             "Low": [10, 10],
             "Open": [11, 12],
             "Close": [11, 14],
             "Volume": [100, 110],
             "Date" : ['1/1/20','1/2/20']}
        df = pd.DataFrame(data = d)
        df['Symbol'] = 'ETH/BTC'
        
        tick_class = aml.DataSet(data = df)
        result = tick_class.get_tick()
        expected = 1
        self.assertEqual(result, expected)
    
    def test_populate_winnings(self):
        if not path.exists("testingdata\\QTUMtestdata.csv"): 
            data = gcd.tryGetDataFrame('QTUM/BTC', exchange=None, timeFrame = '1d', inSince='2020-03-25 00:00:00') #2020-3-25 gets us 3-27 as the first day which is what we want. Don't know why?
            data.index = pd.to_datetime(data.index, unit='ms', utc=True)
            test_set = aml.DataSet(data = data.loc['2020-03-27':'2020-04-12',:]) 
            test_set.data.to_csv("testingdata\\QTUMtestdata.csv")
        else:
            test_set = aml.DataSet(dataFile = "testingdata\\QTUMtestdata.csv")
        takeTrade = [False,False,True,False,True,False,False,False,True,True,True,False,False,False,False,False,False]
        test_set.data["TakeTrade"] = takeTrade
        exp = [-0.00000380, -0.00000660, -0.000004, 0.0000102]#-0.0000058] <---value without intrabar evaluation
        expected = np.array(exp)
        result = test_set.populate_winnings(test_set.data["TakeTrade"]).round(9)
        result = result['Win/Loss Amt'].values
        np.testing.assert_array_equal(result, expected)
        
        
        #test taking every trade
        result = test_set.populate_winnings(test_set.data["TakeTrade"], True).round(9)
        result = result['Win/Loss Amt'].values
        exp = [-0.00000380, -0.00000660, -0.000004, 0.0000102, 0.0000063]
        expected = np.array(exp)
        np.testing.assert_array_equal(result, expected)
        
        # Timestamp   Open       High        Low      Close        TakeTrade                                                 
        # 2020-03-27  0.0001895  0.0001923  0.0001860  0.0001894   False
        # 2020-03-28  0.0001894  0.0001976  0.0001877  0.0001943   False
        # 2020-03-29  0.0001945  0.0001956  0.0001920  0.0001941   True
        # 2020-03-30  0.0001940  0.0001965  0.0001847  0.0001875   False
        # 2020-03-31  0.0001874  0.0001918  0.0001854  0.0001887   True
        # 2020-04-01  0.0001887  0.0001925  0.0001837  0.0001841   False
        # 2020-04-02  0.0001842  0.0001878  0.0001815  0.0001866   False
        # 2020-04-03  0.0001864  0.0001888  0.0001842  0.0001884   False
        # 2020-04-04  0.0001884  0.0001896  0.0001858  0.0001883   True
        # 2020-04-05  0.0001881  0.0001898  0.0001842  0.0001858   True
        # 2020-04-06  0.0001858  0.0001937  0.0001832  0.0001932   True
        # 2020-04-07  0.0001934  0.0001948  0.0001892  0.0001912   False
        # 2020-04-08  0.0001912  0.0002065  0.0001904  0.0002040   False
        # 2020-04-09  0.0002041  0.0002073  0.0002002  0.0002026   False
        # 2020-04-10  0.0002026  0.0002053  0.0001912  0.0001954   False
        # 2020-04-11  0.0001954  0.0002008  0.0001930  0.0001960   False
        # 2020-04-12  0.0001959  0.0002000  0.0001949  0.0001972   False

                
        

if __name__ == "__main__":
    unittest.main()
    
        
