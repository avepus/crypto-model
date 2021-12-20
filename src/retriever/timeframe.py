

from typing import ClassVar
from datetime import timedelta


class Timeframe:
    """timedelta with more convenient initialization and __str__ methods"""
    timeframe: timedelta
    TIMEFRAME_MAP_SEC: ClassVar[dict[int]] = {
        'S': 1,
        'M': 60,
        'H': 3600,
        'D': 86400,
        'W': 86400*7
    }

    def __init__(self, timeframe: timedelta):
        self.timeframe = timeframe
    
    @classmethod
    def from_string(cls, timeframe: str):
        timeframe = timedelta(seconds=cls.convert_timeframe_string_to_sec(timeframe))
        return cls(timeframe)

    @classmethod
    def from_seconds(cls, seconds: int):
        timeframe = timedelta(seconds=seconds)
        return cls(timeframe)

    @classmethod
    def convert_timeframe_string_to_sec(cls, timeframe: str):
        """Converts timeframe string to seconds"""
        #set timeframe to the alpha character in the string
        timeframe_symbol = ''.join(char for char in timeframe.upper() if not char.isdigit())
        #set factor to the digits
        digits = ''.join(char for char in timeframe if char.isdigit())
        factor = int(digits) if digits else 1
        return cls.TIMEFRAME_MAP_SEC[timeframe_symbol] * factor

    def __str__(self):
        """implents the timedelta string representation"""
        return self.timeframe.__str__()

    def get_timeframe_seconds(self):
        return self.timeframe.total_seconds()

    def get_timeframe_name(self):
        """
        Converts a timeframe to a name with the highest increment
        and number of increments like 4H
        """
        increment_symbol = self.get_highest_time_increment_symbol()
        increments = int(self.get_timeframe_seconds() / self.TIMEFRAME_MAP_SEC[increment_symbol])
        return str(increments) + increment_symbol

    def get_timeframe_table_name(self):
        """Converts a timeframe string to a the highest time increment"""
        return 'TIMEFRAME_' + self.get_timeframe_name()

    def get_highest_time_increment_symbol(self) -> str:
        seconds = self.get_timeframe_seconds()
        if seconds % self.TIMEFRAME_MAP_SEC['D'] == 0: return 'D'
        if seconds % self.TIMEFRAME_MAP_SEC['H'] == 0: return 'H'
        if seconds % self.TIMEFRAME_MAP_SEC['M'] == 0: return 'M'
        else: raise ValueError(f"timeframe value of {seconds} seconds is invalid")

    def __eq__(self, other):
        if type(other) is type(self):
            return self.timeframe == other.timeframe
        return False
    