import unittest
import os
import tempfile
import sqlite3
from src.utils.database import DatabaseManager

class TestMigration(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(self.temp_db)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                trade_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)

    def test_migrate_and_insert(self):
        dbm = DatabaseManager(db_path=self.temp_db)
        dbm.init_database()
        conn = sqlite3.connect(self.temp_db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(trades)")
        cols = [row[1] for row in cur.fetchall()]
        conn.close()
        self.assertIn('order_status', cols)
        self.assertIn('net_amount', cols)
        ok = dbm.insert_trade({
            'trade_date': '2025-01-01 10:00:00',
            'stock_code': '000001',
            'stock_name': '测试',
            'trade_type': 'BUY',
            'quantity': 100,
            'price': 10.0,
            'amount': 1000.0,
            'order_status': '全部成交'
        })
        self.assertTrue(ok)

if __name__ == '__main__':
    unittest.main()
