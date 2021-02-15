"""
Created on Dec 6th

@author: Avery And Jake

Website References:
different model options - https://www.kaggle.com/kashnitsky/topic-9-part-1-time-series-analysis-in-python
forecasting bitcoin with python - https://www.kaggle.com/vennaa/notebook-forecasting-bitcoins

"""



# Import Data
import warnings  # do not disturb mode
import sklearn

warnings.filterwarnings('ignore')

import numpy as np  # vectors and matrices
import pandas as pd  # tables and data manipulation
import matplotlib.pyplot as plt  # plots
from sklearn.metrics import r2_score, median_absolute_error, mean_absolute_error
from sklearn.metrics import median_absolute_error, mean_squared_error, mean_squared_log_error


# Global presets
csv_source = 'ohlcv_data\MarketDataVIBBTC.csv'



def mean_absolute_percentage_error(y_true, y_pred):
    '''
        MAPE for error analysis
    '''
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def main():
    '''
    Returns - Currently just data exploration
    -------
    '''

    df = pd.read_csv(csv_source, index_col=['Time_Converted'],parse_dates=['Time_Converted']) # Time_Converted is a column that was manually added to the dataset with the formula =(A2/86400000)+25569 to convert to excel date. Add code to complete automatically


    print(df.head())
    plt.figure(figsize=(15, 7))
    plt.plot(df.Open)
    plt.plot(df.Close)
    plt.title('Historicalical Open/Close')
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(15, 7))
    plt.plot(df.Volume)
    plt.title('Historicalical Volume')
    plt.grid(True)
    plt.show()

main()