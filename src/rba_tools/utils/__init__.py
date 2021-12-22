from re import split
from pandas import DataFrame
from typing import Type
timeframe_map = { 'S' : 1,
                  'M' : 60,
                  'H' : 60*60,
                  'D' : 60*60*24 }

def convert_timeframe_to_sec(timeframe_string):
    """Converts timeframe string to seconds
    
    Parameters:
        timeframe_string (str) -- timeframe string, e.g. 'm' for one minute or '4h' for 4 hours

    Returns:
        The timeframe value in seconds
    """
    timeframe_string = timeframe_string.upper()
    #set timeframe to the alpha character in the string
    timeframe = ''.join(char for char in timeframe_string if not char.isdigit())
    #set factor to the digits
    digits = ''.join(char for char in timeframe_string if char.isdigit())
    factor = int(digits) if digits else 1
    return timeframe_map[timeframe] * factor

def get_timeframe_name_from_str(timeframe_string: str) -> str:
    """Converts a timeframe string to a the highest time increment"""
    secs = convert_timeframe_to_sec(timeframe_string)
    return get_timeframe_name_from_seconds(secs)

def get_timeframe_name_from_seconds(seconds: int) -> str:
    """Converts a timeframe string to a the highest time increment"""
    increment_symbol = get_highest_time_increment_symbol(seconds)
    increments = int(seconds / timeframe_map[increment_symbol])
    return str(increments) + increment_symbol

def get_table_name_from_str(timeframe_string: str) -> str:
    return "TIMEFRAME_" + get_timeframe_name_from_str(timeframe_string)

def get_table_name_from_dataframe(df: type[DataFrame]) -> str:
    secs = get_timeframe_in_seconds_from_df(df)
    return "TIMEFRAME_" + get_timeframe_name_from_seconds(secs)

def get_timeframe_in_seconds_from_df(df: type[DataFrame]) -> int:
    """given a DataFrame, returns the minimum number of seconds between the indicies"""
    minimum_timedelta = min(df.index.to_series().diff().dropna())
    return int(minimum_timedelta.total_seconds())

def get_highest_time_increment_symbol(seconds) -> str:
    if seconds % timeframe_map['D'] == 0: return 'D'
    if seconds % timeframe_map['H'] == 0: return 'H'
    if seconds % timeframe_map['M'] == 0: return 'M'
    else: raise ValueError(f"timeframe value of {seconds} seconds is invalid")


def convert_timeframe_to_ms(timeframe_string):
    """Converts timeframe string to milliseconds"""
    return convert_timeframe_to_sec(timeframe_string) * 1000

if __name__ == "__main__":
    pass
