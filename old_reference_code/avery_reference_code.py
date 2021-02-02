# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 18:26:54 2020

@author: Avery
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import getCryptoData as gcd

class DataSet:
    
    NEEDED_COLUMNS = ["Open", "High", "Low", "Close", "Volume", "Symbol"]
    TRAILING_STOP = 1
    tick = None
    
    def __init__(self, data=None, dataFile=None, stopLossFunction=None, precision=None):
        """
        Initialize DataSet object

        Parameters
        ----------
        data : dataframe, optional
            dataframe to use as the dataset. The default is None.
            Not needed if dataFile is passed in
        dataFile : str, optional
            file path to read data frome. The default is None.
            Not needed if data is passed in
        stopLossFunction : obj, optional
            function to calculate the stop-loss. The default is None.
        precision : int, optional
            decimal precision. The default is None.
            Not needed if using dataFile

        Returns
        -------
        None.

        """
        if data is not None:
            self.data = data.copy()
            if (type(self.data.index) != pd.DatetimeIndex): #if index is not a datetime then attempt to make it so
                self.set_data_timestamp_index()
            self.set_tick()
        self.dataFile = dataFile
        if self.dataFile is not None:
            self.load_csv()
        self.stopLossFunction = stopLossFunction
        if self.stopLossFunction is None:
            self.stopLossFunction = self.trailing_stop
        if not hasattr(self, 'symbol'):
            self.symbol = self.data.at[self.data.index[0],'Symbol']
        self.figure = self.plot()
        #enhancement: check if data is valid at this point
    
    def trailing_stop(self, time, bars=None):
        """
        get the tailing stop value

        Parameters
        ----------
        time : dateTime
            datetime for which to obtain the trailing stop value.
        bars : TYPE, optional
            bars back to get trailing stop. The default is trailing_stop.

        Returns
        -------
        float
            tailling stop value.

        """
        if bars is None:
            bars = self.TRAILING_STOP
        colLoc = self.data.columns.get_loc("Low")
        rowLoc = self.data.index.get_loc(time)
        low = min(self.data.iloc[rowLoc-bars:rowLoc,colLoc])
        return round(low - self.tick, 10)
        
        
    
    def changeColumnToDatetime(self, col, unit=None, utc=False):
        """
        Change a specified column of data from a string to a datetime

        Parameters
        ----------
        col : str
            column to converst from string to datetime.
            
        Returns
        -------
        None.
        
        """
        if (type(self.data.dtypes[col]) == np.datetime64):
            print("Already in date form")
            return
        self.data.loc[:,col] = pd.to_datetime(self.data.loc[:,col], unit=unit)
    
    def load_csv(self):
        """Reload data from dataFile and set index dateTime"""
        
        self.data = pd.read_csv(self.dataFile)
        self.set_data_timestamp_index() #change to function
        self.symbol = self.data.at[self.data.index[0],'Symbol']
        self.set_tick()
        self.figure = self.plot()
    
    def set_data_timestamp_index(self):
        col = None
        unit = None
        if ("Date" in self.data.columns): #needs unit test
            col = "Date"
        if ("Timestamp" in self.data.columns): #needs unit test
            col = "Timestamp"
            unit = 'ms'
        try:
            self.changeColumnToDatetime(col, unit)
        except ValueError:
            self.changeColumnToDatetime(col)
        if col is not None:
            self.data.set_index(col, inplace=True)
    
    def addMovingAverage(self, period, col="Close", header=None):
        """
        Add the moving average to a datafrom based on input column

        Parameters
        ----------
        period : int
            the peiod of the moving average.
        col : str, optional
            the column to compute the moving average of. The default is "Close".

        Returns
        -------
        string of label created

        """
        if header is None:
            header = str(col) + " SMA(" + str(period) + ")"
        self.data[header] = self.data[col].rolling(period).mean()
        return header
    
    def addStochastic(self, period, kSmooth, d, close="Close", high="High", low="Low"):
        """
        Calculate and append the stochastic indicator to a dataframe object.

        Parameters
        ----------
        period : int
            the length of the lookback.
        kSmooth : int
            smoothing value for %K.
        d : int
            smoothing value for %D.
        close : string, optional
            column name to use for the Close. The default is "Close".
        high : string, optional
            column name to use for the High. The default is "High".
        low : string, optional
            column name to use for the Low. The default is "Low".

        Returns
        -------
        None.

        """
        kVals = calc_Stochastic_K(self.data, period, close, high, low)
        percentKVals = movingAveragePD(kVals, kSmooth)
        header = 'Stochastic %K (' + str(period) + ',' + str(kSmooth) + ',' + str(d) + ')'
        self.data[header] = percentKVals
        header = 'Stochastic %D (' + str(period) + ',' + str(kSmooth) + ',' + str(d) + ')'
        self.data[header] = movingAveragePD(percentKVals, d)
        
    def addMACD(self, fast, slow, signalSmooth, column = "Close"):
        """
        Calculate and append the MACD indicator to a dataframe object.

        Parameters
        ----------
        fast : int
            period of fast ema.
        slow : int
            period of slow ema.
        signalSmooth : int
            smoothing used to calculate signal line.
        column : string, optional
            column name to use for input. The default is "Close".

        Returns
        -------
        None.

        """
        macdVals = calc_MACD(self.data[column], fast, slow)
        signalVals = emaPD(macdVals, signalSmooth)
        histVals = macdVals - signalVals
        header = "MACD (" + str(fast) + "," + str(slow) + "," + str(signalSmooth) + ")"
        self.data[header] = macdVals
        self.data[header + " Signal"] = signalVals
        self.data[header + " Histogram"] = histVals
    
    def dropColumn(self, label):
        """Removes column by label or column number"""
        if type(label == int):
            label = self.data.columns[label]
        if (label in self.NEEDED_COLUMNS):
            print("Cannot remove ", label, ". Column is reserved.", sep = "")
        else:
            self.data.drop(label, axis=1, inplace=True)
    
    def addPercentageChange(self, start="Open", end="Close"):
        """
        Add a percentage change series to a dataframe

        Parameters
        ----------
        start : string, optional
            column label for the numerator. The default is "Open".
        end : string, optional
            column label for the denominator. The default is "Close".

        Returns
        -------
        string of label created.

        """
        retSeries = self.data[start].rsub(self.data[end])
        retSeries = self.data[start].rdiv(retSeries)
        retSeries = retSeries * (100)
        header = start + "/" + end + "%Change"
        self.data[header] = retSeries
        return header
    
    def dropna(self):
        """Drops NaN values from data"""
        self.data.dropna(inplace=True)
        
    def tradeEntered(self, time, entryPrice):
        high = np.round(self.data.loc[time,"High"], 10)
        open = np.round(self.data.loc[time,"Open"], 10)
        if (high > entryPrice and open < entryPrice):
            return True
        return False

    def evaluateTrade(self, entryTime, entryPrice, target=None, stopLoss=0, stopLossFun=True):
        """
        Get winnings/losings from a trade
    
        Parameters
        ----------
        entryTime : timestamp
            timestamp of bar entry trade placed
        entryTrigger : float
            stop order entry price
        target : float, optional
            target exit price. The default is None
        stopLoss : float, optional
            stop order exit price. The default is 0
        stopLossFun : function, optional
            function that takes a dataFrame and time and returns the stop loss
            The default is None
    
        Returns
        -------
        (datetime, float)
    
        """
        try:
            evalTime = self.getNextDateTime(entryTime)
        except (IndexError): #if the next bar is out of bounds then we don't enter trade
            return (entryTime, 0)
        if not self.tradeEntered(evalTime, entryPrice):
            return (entryTime, np.nan)
        for t in self.data.loc[evalTime:,:].index:
            if stopLossFun:
                stopLoss = self.stopLossFunction(t)
            low = self.data.loc[t,"Low"]
            high = self.data.loc[t,"High"]
            opn = self.data.loc[t,"Open"]
            if (stopLoss >= low and t == evalTime):
                if self.stopLossHitAfterEntry(t, stopLoss, entryPrice):
                    loss = round(stopLoss - entryPrice, 10)
                    return (t, loss)
                else:
                    continue
            if (opn < stopLoss): #handle when we open below stop-loss and take a bigger loss than the stop-loss
                loss = round(opn - entryPrice, 10)
                return (t, loss)
            if (stopLoss >= low and target is not None and target <= high):
                return (t, np.nan)
            if (stopLoss >= low):
                loss = np.round(stopLoss - entryPrice, 10)
                return (t, loss)
            if (target is not None and target <= high):
                gain = np.round(target - entryPrice, 10)
                return (t, gain)
        return (t, np.nan)
    
    def stopLossHitAfterEntry(self, startTime, stopLoss, entryPrice):
        """
        Performs analysis of trades entered and existed on the same bar
        
        This is necessary to determine if the stop loss was hit after the entry
        was triggered and it was an instant loss or if we made it to the next bar.
        Returns
        -------
        True if the stop loss was hit after the entry within the same bar
            Enhancement needed for recursive call
            Enhancement needed to account for hitting target
        """
        endTime = self.getNextDateTime(startTime)
        if (not hasattr(self, 'detailData')) or (endTime not in self.detailData.index):
            self.detailData = gcd.tryGetDataFrame(self.symbol, timeFrame = '1h', inSince=str(startTime))
            self.detailData.index = pd.to_datetime(self.detailData.index, unit='ms')
        entryTime = None
        for t in self.detailData.iloc[self.detailData.index.get_loc(startTime):self.detailData.index.get_loc(endTime),:].index: #this disgusting code enables us to go up to 23:00 without including 00:00 the next day
            if self.detailData.at[t,"High"] > entryPrice and entryTime == None:
                entryTime = t
            if self.detailData.at[t,"Low"] < stopLoss and t == entryTime:
                return True #Not correct to assume this is a loss. Enhancement here is to recursively call into the same function on a smaller timeframe
            if self.detailData.at[t,"Low"] < stopLoss and entryTime is not None:
                return True
        return False
    
    def getNextDateTimeI(self, time, offset=1):
        """Given a datetime, get the next index of a DatetimeIndex"""
        return self.data.index.get_loc(time) + offset
    
    def getNextDateTime(self, time, offset=1):
        """Given a datetime, get next datetime of of DatetimeIndex"""
        return self.data.index[self.getNextDateTimeI(time, offset)]
        
    
    def populate_winnings(self, takeTrade, takeAll=False):
        """
        Takes trades per the input series and a creates a results dataframe

        Future Enhancements:
            take in a target offset amount
            take in a target as precent of entry - stoploss
        Parameters
        ----------
        takeTrade : pandas.Series
            boolean series indicating if a trde should be submitted for a time
        takeAll : takeAll
            boolean indicating whether new trades can be taken while a trade is active

        Returns
        -------
        Dataframe.

        """
        df = self.data.copy()
        time = self.data.index[0]
        for t in self.data.index[:-1]: #exclude the last index as we cannot enter trades on the last bar
            if takeTrade.at[t]:
                if (t >= time or takeAll): #don't take another trade if there's an active trade
                    entryPrice = self.data.loc[t,"High"] + self.tick
                    (time, gainOrLoss) = self.evaluateTrade(t, entryPrice)
                    enteredTime = self.getNextDateTime(t)
                    df.at[t,'Entry Time'] = enteredTime
                    df.at[t,'Exit Time'] = time
                    df.at[t,'Entry Price'] = entryPrice
                    df.at[t,'Win/Loss Amt'] = gainOrLoss
                    df.at[t,'Trade High'] = df.loc[t:self.getNextDateTime(time,offset=-1),'High'].max()
        #I verified that doing these after instead of in the loop is faster
        #Throws key error if no trades entered. Enhancement could be to handle that
        df['Win/Loss %'] = df['Win/Loss Amt'] / df['Entry Price'] * 100
        df['Win/Loss %'] = df['Win/Loss %'].round(2)
        df['Exit Price'] = df['Entry Price'] + df['Win/Loss Amt']
        df['Rolling Gain'] = ((df['Win/Loss Amt'] / df['Entry Price']) + 1).cumprod()
        df.dropna(inplace=True)
        return df
    
    def get_tick(self):
        """
        Get the value for one tick from the current dataset

        Returns
        -------
        int

        """
        df = self.data[["High","Low","Close","Open"]]
        df = round(df - df.astype("int"), 9)
        series = df.astype("str").stack()
        splitStr = series.str.split(".", expand=True)
        #handle case when there is no decimal place
        if (len(splitStr.columns) <= 1):
            return 1
        precision = splitStr[1].str.len().max()
        return 10.0 ** (-1 * precision)
    
    def set_tick(self):
        """set the value for one tick from the current dataset"""
        self.tick = self.get_tick()
        
    def consecutive_Bar_Change(self, label="Consecutive Bar Change", percent=False):
        """
        Calculates change from open to close of consecutive green/red days

        Parameters
        ----------
        label : str, optional
            Label for the new column. The default is "Consecutive Bar Change".
        percent : bool, optional
            Show the Amount as a % change from open. The default is False.

        Returns
        -------
        None.

        """
        consecutiveArray = consecutiveBarCount(self.data)
        diffs = np.zeros_like(consecutiveArray, dtype=float)
        i = -1
        for t in self.data.index:
            i += 1
            offset = -1 * abs(consecutiveArray[i])
            offsetTime = self.getNextDateTime(t, offset)
            diff = self.data.at[t,"Close"] - self.data.at[offsetTime,"Open"]
            if percent:
                diff = diff / self.data.at[offsetTime,"Open"]
            diffs[i] = diff
        self.data[label] = diffs
    
    def get_candlestick_plot(self):
        return go.Candlestick(x=self.data.index,
                open=self.data['Open'],
                high=self.data['High'],
                low=self.data['Low'],
                close=self.data['Close'],
                name = self.symbol)
    
    def defaultMAs(self, plots):
        mas = {50: 'red', 100 : 'blue', 200 : 'orange'}
        for ma, color in mas.items():
            header = self.addMovingAverage(ma)
            plots.append(go.Scatter(x=self.data.index,
                                    y=self.data[header],
                                    line=dict(color=color, width=1),
                                    name=str(ma) + ' SMA'))
    
    def plot(self, candles=True, defaultMA=False, **args):
        plots = []
        if candles:
            plots.append(self.get_candlestick_plot())
        if defaultMA:
            self.defaultMAs(plots)
        for key in args:
            if ('ma' in key):
                (ma, color) = args[key]
                header = self.addMovingAverage(ma)
                plots.append(go.Scatter(x=self.data.index,
                                        y=self.data[header],
                                        line=dict(color=color, width=1),
                                        name=str(ma) + ' SMA'))
        return go.Figure(data = plots,
                layout={
                'title': self.symbol,
                'plot_bgcolor': '#111111',
                'paper_bgcolor': '#111111',
                'xaxis' : {'rangeslider': {'visible': False}},
                'font': {'color': '#7FDBFF'}
            })
    
        #end of DataSet class
            
    
#************STRATEGIES****************
#Strategy code does a series of calculations on a dataset or series
#and populates the results of running that trading strategy on the data

def strategyPercentOfDaysHighLowThreshold(dataset, days, threshold):
    """
    generate crtieria based on a low difference between the highs and lows

    The idean behind this is that if the low and high are close together
    over the course of several days then the we are due for a breakout
    Parameters
    ----------
    days : int
        number of days to look back at highs and lows.
    threshold : float
        ratio of lowest low / highest high that must be met

    Returns
    -------
    pandas.Series
        series to be used as a mask in the data.

    """
    dataset.addPercentageChange()
    HighLowDayPercentDiff = dataset.data["Low"].rolling(days).min() / dataset.data["High"].rolling(days).max()
    header = 'HighLow' + str(days) + 'PercentDiff'
    dataset.data[header] = HighLowDayPercentDiff
    return HighLowDayPercentDiff > threshold
    
def strategyCrossover(series, crossValue, fromBelow=True):
    """
    Strategy based on a series crossing over a value

    Parameters
    ----------
    series : pandas.Series
        The series to check for a crossover.
    crossValue : pandas.Series/numpy.array/float
        the value or values to check for a crossover.
    fromBelow : bool, optional
        Default is True which means to check for crossover from below to above
        Flase checks for crossover from above to below

    Returns
    -------
    pandas.Series
        series to be used as a mask in the data.

    """
    if fromBelow:
        return (np.roll(series,1) < np.roll(crossValue,1)) & (series > crossValue)
    else:
        return (np.roll(series,1) > np.roll(crossValue,1)) & (series < crossValue)

def strategySMADirection(dataset, sma=50, up=True):
    """
    Strategy that is based on direction of SMA

    Parameters
    ----------
    dataset : class
        dataset to run strategy on.
    sma : int, optional
        simple moving average length. The default is 50.
    up : bool, optional
        if direction is down. The default is False which means direction is up

    Returns
    -------
    pd.Series
        bool series of days to take trades on

    """
    head = str(sma) + ' SMA'
    dataset.addMovingAverage(sma,header=head)
    dataset.data[head + ' Slope'] = calcSlope(dataset.data[head])
    if up:
        return dataset.data[head + ' Slope'] > 0
    else:
        return dataset.data[head + ' Slope'] < 0

def strategyPercentOfRollingVolAvg(dataset, days, threshold, above=True):
    """
    Checks the ratio of today's volume to the average is above or below a threshold

    Parameters
    ----------
    dataset : class
        dataset to run strategy on.
    days : int
        days the average represents.
    threshold : TYPE
        DESCRIPTION.
    above : bool, optional
        if the ratio must be above the treshold. Default is True

    Returns
    -------
    pd.Series
        bool series of days to take trades on

    """
    head = str(days) + ' Day Vol MA'
    dataset.addMovingAverage(days, col='Volume', header=head)
    dataset.data[head + ' / Vol'] = dataset.data['Volume'] / dataset.data[head]
    return dataset.data[head + ' / Vol'] > threshold

def myFirstStrategry(dataset):
    """
    This is my first strategy I created to run on a dataset

    This is based solely off of the 5 day low / 5 day low > 92.5%
    Parameters
    ----------
    dataset : class
        dataset to run strategy on.

    Returns
    -------
    pd.Series
        bool series of days to take trades on

    """
    dataset.addMovingAverage(5, col='Volume', header='5DayVolMA')
    dataset.data['Prev Day % of 5DayVolMA'] = dataset.data['5DayVolMA'] / dataset.data['Volume'] * 100
    dataset.addMovingAverage(50,header='50 SMA')
    dataset.data['50 SMA Slope'] = calcSlope(dataset.data['50 SMA'])
    return (strategyPercentOfDaysHighLowThreshold(dataset,5, 0.925)) & (dataset.data.index > '2020-01-01')

def strategyFromAndToDateRange(dataset, start=None, end=None):
    if start is not None:
        retStart = dataset.data.index > start
        if end is None:
            return retStart
    if end is not None:
        retEnd = dataset.data.index < end
        if start is None:
            return retEnd
    return retStart & retEnd
    

def current_strategy(dataset):#left off here want to take volume and SMA into account
    """
    This is the currently tested strategy used in create_summary_file

    This does whatever needs to be done to the dataset and returns a bool
    series of days to take trades on
    Parameters
    ----------
    dataset : class
        dataset to run strategy on.

    Returns
    -------
    pd.Series
        bool series of days to take trades on

    """
    return ((dataset.data.index > '2020-01-01') &
        (strategyPercentOfDaysHighLowThreshold(dataset,5, 0.925)) &
        (strategyPercentOfRollingVolAvg(dataset, 5, 1.6)) &
        (strategySMADirection(dataset, sma=50)))

def expandSignal(series, signalLength):
    """
    Extends each True bool in the series to a specified length

    Example input of 3 means that every True in the input series would have
    the following three bars marked True as well. This is used a means to
    expand rare signals like crossovers to hold true for multiple bars.    
    This can not be propagated backwards because that means seeing the future
    
    Parameters
    ----------
    series : pandas.Series
        The series to check propagate True bool foward
    signalLength : int
        The number of bars each True should be expanded to

    Returns
    -------
    pd.Series
        bool series of days to take trades on

    """
    result = series.copy()
    for d in result.loc[result == True].index:
        end = result.index[result.index.get_loc(d) + signalLength - 1]
        result.loc[d:end] = True
    return result
        

#end of strategies

def create_summary_file(directory, fileName="programoutput.csv"):
    outputFileName = directory + "\\" + fileName
    file = open(outputFileName, mode='w')
    file.close()
    write = True
    for filename in os.listdir(directory):
        if (filename.endswith(".csv") and 'MarketData' in filename):
            file = directory + '\\' + filename
            print(file)
            dataset = DataSet(dataFile = file)
            try:
                result = dataset.populate_winnings(myFirstStrategry(dataset))
            except:
                print('file:',file,'did had no trades.')
                continue
            result['File'] = [file for x in result.index]
            result['Highest % Gain Possible'] = (result['Trade High'] - result['Entry Price']) / result['Entry Price'] * 100
            result.to_csv(outputFileName, mode = 'a', header=write)
            write=False

def count_tickers(data):
    """
    Count the number of tickers in a yfinance.download

    Parameters
    ----------
    data : pandas DataFrame
        dataFrame returned by yfinance.download(...)

    Returns
    -------
    int
    """
    count = 0
    metric = data.columns[0][0]
    for col in data.columns:
        if (col[0] == metric):
            count += 1
    return count

def clean_columns(data):
    """
    Untuple the dataframe data from a yfinance.download call.
    
    Downloading mutliple tickers simultaneously using yfinance creates a
    dataframe tuple columns in the form (<metric>, <ticker).
    This function moves the ticker to a column and returns a list of
    dataframes in which the ticker has been moved to a column.
    Parameters
    ----------
    data : pandas DataFrame
        dataFrame returned by yfinance.download(...)

    Returns
    -------
    list
    """
    frameList = []
    for i in range(0, count_tickers(data)):
        curTicker = data.columns[i][1] #ticker is always the second element of the tuple column
        df = data.copy()
        for col in df.columns:
            if (col[1] != curTicker):
                df = df.drop(col, axis=1)
        df.columns = [x[0] for x in df.columns]
        df["Ticker"] = [curTicker for x in df['Close']]
        frameList.append(df)
    return frameList

def movingAverageNP(npAry, period):
    """
    Calculate and return the moving average of a numpy array or pandas series
    
    Raises AttributeError if wrong type is passed in
    Parameters:
        npAry (np.array) -- numpy array to calculate moving average for
        period (int) -- the length of the moving average
    """
    retAry = np.nancumsum(npAry, dtype=float)
    retAry[period:] = retAry[period:] - retAry[:-period]
    retAry[:period-1] = np.nan
    return retAry / period

def movingAveragePD(pdSeries, period):
    """
    Calculate and return the moving average of a numpy array or pandas series
    
    Parameters:
        valList (np.array, pd.series) -- moving average is calculated for this
        period (int) -- the length of the average
    """
    return pdSeries.rolling(period).mean()

def emaNP(valList, period):
    """
    Calculate and return the exponential moving average of a numpy array
    
    Parameters:
        valList (np.array) -- numpy array to calculate moving average for
        period (int) -- the length of the average
    """
    emaVals = np.empty_like(valList)
    emaVals[0] = valList[0] #nothing to average for first value
    alpha = (2 / (period + 1))
    for i in range(1, len(valList)):
            emaVal = ((valList[i] - emaVals[i - 1])) * float(alpha) + emaVals[i - 1]
            emaVals[i] = emaVal
    return emaVals

def emaPD(pdSeries, period):
    """
    Calculate and return the exponential moving average of a numpy array
    
    Parameters:
        pdSeries (pd.series) -- pandas series to calculate moving average for
        period (int) -- the length of the average
    """
    return pdSeries.ewm(span=period, adjust=False).mean()

#calculates the current value minus the last value in a numpy array
#this needs to use numpy.roll
def calcSlope(npAry):
    """
    Calculate and return the instantaneous slope of a numpy array.
    
    Parameters:
        valList (np.array) -- numpy array to calculate slopes for
    """
    ret = npAry - np.roll(npAry, 1)
    ret[0] = 0
    return ret

def calc_Stochastic_K(df, period, close="Close", high="High", low="Low"):
    """
    Calculate unsmoothed stochastic K for a dataframe object.
    
    Returns a pandas Series
    Parameters:
        df (dataFrame) -- dataframe to calculate and append the indicator to
        period (int) -- the length of the lookback
        close (str) -- the "close" column used in stochastic calculation
        high (str) -- the "high" column used in stochastic calculation
        low (str) -- the "low" column used in stochastic calculation
    """
    closeSeries = df[close]
    highSeries = df[high].rolling(period).max()
    lowSeries = df[low].rolling(period).min()
    return (closeSeries - lowSeries) / (highSeries - lowSeries)

def calc_MACD(series, fast, slow):
    fastEMA = emaPD(series, fast)
    slowEMA = emaPD(series, slow)
    return fastEMA - slowEMA

#populate successes. Populate array with 1 if entryColumn value + risk*targetPercent is hit
#before hitting min of barRisk
#add max stop loss ns stop loss isn't giant
#add an entry_offset and only count if it's filled the next day.
    #this would require a success (1) failure (-1) and no entry (0)
def addLongSuccess(df, barRisk, targetPercent, entryColumn = "Close"):
    """
    Calculate and append a column win/loss column to a dataframe object.
    
    The entry is the value of entryColumn for the current bar.
    The minimum of the last "barRisk" bars as the stop loss.
    The first target is defined as follows:
        (entry - stop-loss) * targetPercent + entry
    If the high of any of the next bars hits the first target before the low
    falls below the stop loss, it is considered a success
    If the firstTarget and stoploss are hit on the same bar, it is not
    considered a success
    Parameters:
        df (dataFrame) -- dataframe to calculate and append the indicator to
        barRisk (int) -- number of bars to look back to calculate stop-loss
        targetPercent (int) -- percentage used to calculate the frist target
        column (string) -- column name to use for entry. Default is "Close"
    """
    successes = np.zeros_like(df[entryColumn].values)
    for i in range(len(df[entryColumn])):
        entry = df[entryColumn][i]
        stopLoss = df["Low"][i - barRisk:i + 1].min()
        risk = entry - stopLoss
        target = risk * targetPercent / 100.0 + entry
        j = i + 1
        success = None
        while (success == None and j < len(df[entryColumn])):
            if (df["Low"][j] < stopLoss):
                success = False
            elif (df["High"][j] >= target):
                success = True
                successes[i] = 1
            j += 1
    header = "Long r=" + str(barRisk) + " " + str(targetPercent) + "%"
    df[header] = successes

#need function to calculate winnings using some first exit and stop loss method

def clearDataLessThan(df, compareVal, col="Date"):
    """
    Return dataframe that has all rows removed with column value < compareVal
    
    Parameters:
        df (dataFrame) -- dataframe who's values will be compared
        compareVal (float, datetime) -- value to compare to df column values
        col (str) -- column indentifier of the column to compare
    """
    indexList = []
    for i in range(len(df[col])): #len(df["Date"])
        if (df[col][i] < compareVal):
            indexList.append(i)
    ret = df.drop(indexList)
    return ret.reset_index(drop = True)

def percentageOfColumn(df, col, percentOfCol):
    """
    Add a percentage of colmn to a dataframe object (col / percentOfCol)
    
    Parameters:
        df (dataframe) -- dataframe to calculate and append the indicator to
        col (str) -- divsor column identifier
        percentOfCol -- dividend column identifier
    """
    retSeries = df[col].rdiv(df[percentOfCol])
    retSeries = retSeries.rmul(100)
    header = col + "% of " + percentOfCol
    df[header] = retSeries

def consecutiveBarCount(df, start = "Open", end = "Close"):
    """
    Add a column for number of positive or negative bars
    
    The count will be negative for consecutive red bars and postive for
    consecutive green bars
    Parameters:
        df (dataframe) -- dataframe to calculate and append the column to
        start (str) -- string identifying the "Open" or starting value
        end (str) -- string identifying the "Close" or the ending value
    """
    diff = df.loc[:,start].rsub(df.loc[:,end])
    retAry = np.zeros_like(diff, dtype=int)
    count = 0
    direction = 0
    retAry[0] = 0
    for i in range(1, len(diff)):
        if (direction <= 0 and diff.iloc[i] > 0):
            count = 0
            direction = 1
        elif(direction >= 0 and diff.iloc[i] < 0):
            count = 0
            direction *= -1
        else:
            count = count + direction
        retAry[i] = count
    return retAry

def createDataSetFromSymbol(symb, exchange=None, timeFrame = '1d', since=None):
    return DataSet (data = gcd.tryGetDataFrame(symb, exchange, timeFrame, since))

if __name__ == '__main__':
    pass
    #myset = DataSet(dataFile = "C:\\Users\\Avery\\temp\\testing.csv")
    create_summary_file('C:\\Users\Avery\\avery-Trading-ML\\avery_Trading_ML\\crypto_data')