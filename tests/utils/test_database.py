import unittest
import os
import tempfile
from src.utils.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    
    def setUp(self):
        # 创建临时数据库文件
        self.temp_db = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(db_path=self.temp_db)
        
    def tearDown(self):
        # 删除临时数据库文件
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
    
    def test_init_database(self):
        """测试数据库初始化功能"""
        self.db_manager.init_database()
        
        # 验证数据库文件是否创建
        self.assertTrue(os.path.exists(self.temp_db))
        
        # 验证表是否创建
        self.db_manager.connect()
        
        # 检查trades表
        self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        self.assertIsNotNone(self.db_manager.cursor.fetchone())
        
        # 检查positions表
        self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='positions'")
        self.assertIsNotNone(self.db_manager.cursor.fetchone())
        
        # 检查market_data表
        self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market_data'")
        self.assertIsNotNone(self.db_manager.cursor.fetchone())
        
        # 检查logs表
        self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        self.assertIsNotNone(self.db_manager.cursor.fetchone())
        
        # 检查chat_history表
        self.db_manager.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        self.assertIsNotNone(self.db_manager.cursor.fetchone())
        
        self.db_manager.disconnect()
    
    def test_insert_trade(self):
        """测试插入交易记录功能"""
        self.db_manager.init_database()
        
        # 准备测试数据
        trade_data = {
            'trade_date': '2024-01-01 10:00:00',
            'stock_code': '000001',
            'stock_name': '平安银行',
            'trade_type': 'BUY',
            'quantity': 100,
            'price': 10.0,
            'amount': 1000.0,
            'brokerage': 5.0,
            'tax': 0.0,
            'net_amount': 995.0,
            'trade_id': 'test_trade_001'
        }
        
        # 插入交易记录
        trade_id = self.db_manager.insert_trade(trade_data)
        
        # 验证插入成功
        self.assertIsNotNone(trade_id)
        
        # 查询插入的记录
        trades = self.db_manager.get_all_trades()
        self.assertEqual(len(trades), 1)
        
        # 验证记录内容
        trade = trades[0]
        self.assertEqual(trade['stock_code'], '000001')
        self.assertEqual(trade['trade_type'], 'BUY')
        self.assertEqual(trade['quantity'], 100)
        self.assertEqual(trade['price'], 10.0)
    
    def test_update_position(self):
        """测试更新持仓功能"""
        self.db_manager.init_database()
        
        # 准备测试数据
        position_data = {
            'stock_code': '000001',
            'stock_name': '平安银行',
            'quantity': 100,
            'avg_cost': 10.0,
            'current_price': 11.0,
            'market_value': 1100.0,
            'profit': 100.0,
            'profit_rate': 10.0
        }
        
        # 更新持仓
        result = self.db_manager.update_position(position_data)
        
        # 验证更新成功
        self.assertTrue(result)
        
        # 查询持仓
        positions = self.db_manager.get_current_positions()
        self.assertEqual(len(positions), 1)
        
        # 验证持仓内容
        position = positions[0]
        self.assertEqual(position['stock_code'], '000001')
        self.assertEqual(position['quantity'], 100)
        self.assertEqual(position['avg_cost'], 10.0)
        
        # 更新持仓（修改数量）
        updated_position_data = position_data.copy()
        updated_position_data['quantity'] = 200
        updated_position_data['avg_cost'] = 10.5
        
        result = self.db_manager.update_position(updated_position_data)
        self.assertTrue(result)
        
        # 查询更新后的持仓
        positions = self.db_manager.get_current_positions()
        self.assertEqual(len(positions), 1)
        
        # 验证更新后的内容
        position = positions[0]
        self.assertEqual(position['quantity'], 200)
        self.assertEqual(position['avg_cost'], 10.5)
    
    def test_add_chat_message(self):
        """测试添加聊天记录功能"""
        self.db_manager.init_database()
        
        # 准备测试数据
        session_id = 'test_session_001'
        role = 'user'
        content = '测试消息内容'
        
        # 添加聊天记录
        result = self.db_manager.add_chat_message(session_id, role, content)
        
        # 验证添加成功
        self.assertTrue(result)
        
        # 查询聊天记录
        chat_history = self.db_manager.get_chat_history(session_id)
        self.assertEqual(len(chat_history), 1)
        
        # 验证记录内容
        message = chat_history[0]
        self.assertEqual(message['session_id'], session_id)
        self.assertEqual(message['role'], role)
        self.assertEqual(message['content'], content)

if __name__ == '__main__':
    unittest.main()