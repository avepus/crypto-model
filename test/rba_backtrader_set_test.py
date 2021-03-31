import unittest
import pandas as pd
#The lines below allow us to import from the parent directory in a hacky way. Technically https://stackoverflow.com/a/50194143 is the "most right" way to do this
import numpy as np
import os
import rba_tools.backtest.rba_backtrader_set as rbs


class Testrbs(unittest.TestCase):

    def test_TrailingStopStrategy(self):
        pass