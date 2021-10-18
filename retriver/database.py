from abc import abstractmethod
import sqlite3
from sqlite3 import Error
from pathlib import Path
from abc import ABC, abstractmethod

class OHLCVDatabase(ABC):
    @abstractmethod
    def __enter__(self):
        """connects to database"""
    
    @abstractmethod
    def __exit__(self):
        """closes connection to database"""

class SQLite3OHLCVDatabase(OHLCVDatabase):

    def __init__(self, test=False):
        db_name = 'ohlcv_sqlite.db'
        if test:
            db_name = 'test_ohlcv_sqlite.db'
        self.database_file = str(Path(__file__).parent) + '\\ohlcv_data\\' + db_name
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.database_file)
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection: self.connection.close()


def create_ohlcv_table():
    sql_create_ohlcv_table = """ CREATE TABLE IF NOT EXISTS OHLCV_DATA (
                                        Symbol string NOT NULL,
                                        Timestamp integer NOT NULL,
                                        Open real NOT NULL,
                                        High real NOT NULL,
                                        Low real NOT NULL,
                                        Close real NOT NULL,
                                        Volume integer NOT NULL,
                                        Is_Final_Row integer,
                                        PRIMARY KEY (Symbol, Timestamp)
                                        CHECK(Is_Final_Row == 0 or Is_Final_Row == 1 or Is_Final_Row is NULL)
                                    ); """
    with OHLCVDatabase() as connection:
        try:
            cursor = connection.cursor()
            cursor.execute(sql_create_ohlcv_table)
        except Error as err:
            print(err)

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
    with OHLCVDatabase() as connection:
        print(connection)

    print("success")
    #if connection is not None:
        #create_ohlcv_table(connection)
    #    insert_ohlcv_row(connection)
        #print_all_ohlcv_data(connection)
    #    connection.close()
    #else:
    #    print("Error! Cannot create database connection.")