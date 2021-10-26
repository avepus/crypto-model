import unittest
import rba_tools.retriver.database as database
import sqlite3

class TestDatabase(unittest.TestCase):

    def test_SQLite3OHLCVDatabase(self):
        with database.SQLite3OHLCVDatabase(True) as connection:
            self.assertEqual(type(connection), sqlite3.Connection)

        with database.SQLite3OHLCVDatabase(True) as connection:
            self.assertEqual(type(connection), sqlite3.Connection)

            

if __name__ == "__main__":
    unittest.main()