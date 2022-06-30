# -*- coding: utf-8 -*-
"""Contains Timeframe class

Created on Sat Nov 01 2021

@author: Avery

"""

from typing import ClassVar
from datetime import timedelta

class Timeframe:
    """timedelta with more convenient initialization and __str__ methods"""
    timeframe: timedelta
    TIMEFRAME_MAP_SEC: ClassVar = {
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
        """create timeframe from a string, e.g. 5m for 5 minutes"""
        timeframe = timedelta(seconds=cls.convert_timeframe_string_to_sec(timeframe))
        return cls(timeframe)

    @classmethod
    def from_seconds(cls, seconds: int):
        """create timeframe from a string, e.g. 5m for 5 minutes"""
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

    def get_timeframe_seconds(self):
        """Retreieve number of seconds in timeframe"""
        return self.timeframe.total_seconds()

    def get_timeframe_table_name(self):
        """Converts a timeframe string to a the highest time increment"""
        return 'TIMEFRAME_' + str(self)

    def get_highest_time_increment_symbol(self) -> str:
        """Rerieves the highest timeframe that the seconds can be divided into"""
        seconds = self.get_timeframe_seconds()
        if seconds % self.TIMEFRAME_MAP_SEC['D'] == 0: return 'D'
        if seconds % self.TIMEFRAME_MAP_SEC['H'] == 0: return 'H'
        if seconds % self.TIMEFRAME_MAP_SEC['M'] == 0: return 'M'
        else: raise ValueError(f"timeframe value of {seconds} seconds is invalid")

    def __str__(self):
        """
        Converts a timeframe to a name with the highest increment
        and number of increments like 4H
        """
        increment_symbol = self.get_highest_time_increment_symbol()
        increments = int(self.get_timeframe_seconds() / self.TIMEFRAME_MAP_SEC[increment_symbol])
        return str(increments) + increment_symbol

    def __eq__(self, other):
        if type(other) is type(self):
            return self.timeframe == other.timeframe
        return False
    