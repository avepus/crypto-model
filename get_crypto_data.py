# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 22:09:42 2020

@author: Avery
"""

import ccxt
import pandas as pd
from time import sleep
from datetime import datetime, timedelta, timezone
from dateutil import parser,tz

def getBinanceExchange():
    """Gets ccxt class for binance exchange"""
    exchange_id = 'binance'
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({
        'timeout': 30000,
        'enableRateLimit': True,
        })

def tryGetDataFrame(symbol, exchange=None, timeFrame = '1d', inSince=None, lastCall=None):
    """
    Attempts to retrieve data from an exchange for a specified symbol
    
    Returns data in a pandas dataframe
    Parameters:
        symbol (str) -- symbol to gather market data on (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt excahnge to retrieve data from. Default is binance
        timeFrame (str) -- timeframe for which to retrieve the data
        inSince (timestamp ms) -- UTC timestamp in milliseconds
        lastCall (timestamp ms) -- timestamp of last call used to limit number of calls
    """
    if type(inSince) == str:
        inSince = timestampToUTCMs(getUTCTimeStamp(inSince))
    if exchange is None:
        exchange = getBinanceExchange()
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    if not exchange.has['fetchOHLCV']:
        print(exchange, "doesn't support fetchOHLCV")
        return pd.DataFrame([], columns=header) #empty dataframe
    now = timestampToUTCMs()
    if lastCall is not None and (now - lastCall) < 1000:
        sleep(1000 - (now - lastCall))
    lastCall = timestampToUTCMs()
    print('lastCall =',lastCall,'fetching data...')
    data = exchange.fetch_ohlcv(symbol, timeFrame, since=inSince)
    df = pd.DataFrame(data, columns=header).set_index('Timestamp')
    df['Symbol'] = symbol
    return df

def getAllTickers(exchange):
    if not (exchange.has['fetchTickers']):
        print("Exchange cannot fetch all tickers")
    else:
        return exchange.fetch_tickers()

def getAllSymbolsForQuoteCurrency(quoteSymbol, exchange):
    """
    Get's list of all currencies with the input quote currency
    
    Returns a list
    Parameters:
        quoteSymbol (str) -- symbol to check base curriencies for (e.g. "BTC")
        exchange (ccxt class) -- ccxt excahnge to retrieve data from
    """
    if "/" not in quoteSymbol:
        quoteSymbol = "/" + quoteSymbol
    ret = []
    allTickers = exchange.fetch_tickers()
    for symbol in allTickers:
        if quoteSymbol in symbol:
            ret.append(symbol)
    return ret

def getAndSaveData(symbols, exchange, since, includeDate='1-1-1900', fileName = "MarketData", timeFrame = '1d', maxCalls=5):
    """
    Attempts to retrieve and save data for a symbol or list of symbols
    
    includeDate is an important parameter to ensure the symbol was active
    for the data we are interested in evaluating.
    Saves data as a csv file
    Parameters:
        symbols (str/list) -- symbol(s) to get market data (e.g. "BCH/BTC")
        exchange (ccxt class) -- ccxt exchange to retrieve data from
        since (str) -- string representation of start date timeframe
        includeDate (str) -- date that must be in returned data
        fileName (str) -- beginning of the file name
    """
    since = timestampToUTCMs(getUTCTimeStamp(since))
    includeStamp = timestampToUTCMs(getUTCTimeStamp(includeDate))
    for symb in symbols:
        sleep(exchange.rateLimit / 1000)
        attempt = 1
        print('Fetching',symb,'market data. call #',attempt,sep='')
        df = tryGetDataFrame(symb, exchange, timeFrame, since)
        if df.empty:
            print('Failed to retrieve',symb,'data')
            continue
        retdf = df
        while (len(df) == 500 and attempt < maxCalls):
            attempt += 1
            newSince=df.index[-1]
            sleep(exchange.rateLimit / 1000)
            print('Fetching ',symb,' market data. call #',attempt,sep='')
            df = tryGetDataFrame(symb, exchange, timeFrame, newSince)
            retdf = retdf.append(df)
        if retdf.loc[includeStamp:,:].empty:
            print(symb,'data did not include',includeDate,'data not saved.')
            if attempt >= maxCalls:
                print('Maximum data retrivals (',maxCalls,') hit.', sep='')
            continue
        file = fileName + symb + ".csv"
        file = file.replace("/", "")
        file = 'crypto_data\\' + file
        retdf.drop_duplicates(inplace=True) #note much easier to drop duplicates than try to prevent them due to potentially different timeframes
        retdf.to_csv(file) #=(A2/86400000)+25569 converts to excel date
        print(symb,"data saved")
        
def getUTCTimeStamp(timeStr=str(datetime.today())):
    return parser.parse(timeStr, default=datetime.utcnow())

def timestampToUTCMs(dateT=None):
    if dateT is None:
        dateT = datetime.now()
    return int(round(dateT.replace(tzinfo = tz.tzutc()).timestamp() * 1000))
    
if __name__ == '__main__':
    exchange = getBinanceExchange()
    symbols = getAllSymbolsForQuoteCurrency("BTC", exchange)
    print(symbols)
    getAndSaveData(['VIB/BTC'], exchange, '7/1/18', '10/30/20')