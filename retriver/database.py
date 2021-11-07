from abc import abstractmethod
from rba_tools.utils import get_table_name_from_dataframe
from typing import Type
import sqlite3
from sqlite3 import Error
from pathlib import Path
from abc import ABC, abstractmethod
from pandas import DataFrame

#moved to get_crypto_data
# class OHLCVDatabase(ABC):
#     @abstractmethod
#     def store_dataframe(self, df: Type[DataFrame], test=False):
#         """stores pandas dataframe data into database"""

#     @abstractmethod
#     def execute_query(self, query: str):
#         """executes an SQL query"""

# class SQLite3OHLCVDatabase(OHLCVDatabase):

#     def __init__(self, test=False):
#         db_file = 'ohlcv_sqlite_test.db' if test else 'ohlcv_sqlite.db'
#         self.database_file = str(Path(__file__).parent) + '\\ohlcv_data\\' + db_file
#         self.connection = None
        
#     def store_dataframe(self, df: Type[DataFrame]):
#         connection = sqlite3.connect(self.get_database_file())
#         table_name = get_table_name_from_dataframe(df)
#         try:
#             df.to_sql(table_name, connection)
#         finally:
#             connection.close()

#     def execute_query(self, query: str):
#         connection = sqlite3.connect(self.database_file)
#         cursor = connection.cursor()
#         try:
#             cursor.execute(query)
#             data = cursor.fetchall()
#         finally:
#             connection.close()
#         return data

#     def get_database_file(self):
#         return self.database_file




# #shouldn't need to create table since pandas.dataframe.to_sql creates it if it doesn't exist
# def create_ohlcv_table():
#     sql_create_ohlcv_table = """ CREATE TABLE IF NOT EXISTS OHLCV_DATA (
#                                         Symbol string NOT NULL,
#                                         Timestamp integer NOT NULL,
#                                         Open real NOT NULL,
#                                         High real NOT NULL,
#                                         Low real NOT NULL,
#                                         Close real NOT NULL,
#                                         Volume integer NOT NULL,
#                                         Is_Final_Row integer,
#                                         PRIMARY KEY (Symbol, Timestamp)
#                                         CHECK(Is_Final_Row == 0 or Is_Final_Row == 1 or Is_Final_Row is NULL)
#                                     ); """
#     with OHLCVDatabase() as connection:
#         try:
#             cursor = connection.cursor()
#             cursor.execute(sql_create_ohlcv_table)
#         except Error as err:
#             print(err)

def insert_ohlcv_row(connection):
    sql = ''' INSERT INTO OHLCV_DATA
            VALUES(:Symbol,:Timestamp,:Open,:High,:Low,:Close,:Volume,:Is_Final_Row)'''
    value_map = {'Symbol' : 'BTC',
                'Timestamp' : 124,
                'Open' : 10.0,
                'High' : 11.1,
                'Low' : 9.9,
                'Close': 10.51,
                'Volume' : 1000,
                'Is_Final_Row' : 0}
    cursor = connection.cursor()
    cursor.execute(sql, value_map)
    connection.commit()
    return cursor.lastrowid

def print_all_ohlcv_data(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM OHLCV_DATA")
    print(cursor.fetchall())

if __name__ == '__main__':
    pass

    print("success")
    #if connection is not None:
        #create_ohlcv_table(connection)
    #    insert_ohlcv_row(connection)
        #print_all_ohlcv_data(connection)
    #    connection.close()
    #else:
    #    print("Error! Cannot create database connection.")