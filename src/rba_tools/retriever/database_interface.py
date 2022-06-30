from abc import ABC, abstractmethod
import pandas as pd
import sqlite3
from rba_tools.retriever.timeframe import Timeframe
import rba_tools.constants as constants
from pathlib import Path

class OHLCVDatabaseInterface(ABC):
    @abstractmethod
    def store_dataframe(self, df: pd.DataFrame, timeframe: Timeframe) -> None:
        """stores pandas dataframe data into database"""

    @abstractmethod
    def get_query_result_as_dataframe(self, query: str, timeframe: Timeframe) -> pd.DataFrame:
        """executes an SQL query and returns results in dataframe"""

class SQLite3OHLCVDatabase(OHLCVDatabaseInterface):

    def __init__(self, test=False):
        db_file = 'ohlcv_sqlite_test.db' if test else 'ohlcv_sqlite.db'
        self.database_file = str(Path(__file__).parent) + '\\ohlcv_data\\' + db_file
        self.connection = None
        
    def store_dataframe(self, df: pd.DataFrame, timeframe: Timeframe):
        self.create_OHLCV_table_if_not_exists(timeframe)
        connection = sqlite3.connect(self.get_database_file())
        table_name = timeframe.get_timeframe_table_name()
        try:
            df.to_sql(table_name, connection, if_exists='append')
        finally:
            connection.close()

    def get_query_result_as_dataframe(self, query: str, timeframe: Timeframe):
        self.create_OHLCV_table_if_not_exists(timeframe)
        connection = sqlite3.connect(self.get_database_file())
        result = constants.empty_ohlcv_df_generator()
        try:
            result = pd.read_sql_query(query, connection, index_col=constants.INDEX_HEADER, parse_dates=[constants.INDEX_HEADER])
        finally:
            connection.close()
        return result

    def create_OHLCV_table_if_not_exists(self, timeframe: Timeframe) -> None:
        table_name = timeframe.get_timeframe_table_name()
        sql_create_ohlcv_table = f""" CREATE TABLE IF NOT EXISTS {table_name} (
                                        Timestamp integer NOT NULL,
                                        Open real NOT NULL,
                                        High real NOT NULL,
                                        Low real NOT NULL,
                                        Close real NOT NULL,
                                        Volume integer NOT NULL,
                                        Symbol string NOT NULL,
                                        PRIMARY KEY (Symbol, Timestamp)
                                    ); """
        connection = sqlite3.connect(self.get_database_file())
        try:
            cursor = connection.cursor()
            cursor.execute(sql_create_ohlcv_table)
        finally:
            connection.close()

    def _execute_query(self, query: str):
        """execute and return data from a query. Meant only for troubleshooting"""
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            data = cursor.fetchall()
        finally:
            connection.close()
        return data

    def get_database_file(self):
        return self.database_file