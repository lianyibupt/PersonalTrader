import unittest
import os
import tempfile
import pandas as pd
from datetime import datetime
from src.data_ingestion.data_importer import DataImporter
from src.utils.database import DatabaseManager

class TestDataImporter(unittest.TestCase):
    
    def setUp(self):
        # 创建临时数据库文件
        self.temp_db = tempfile.mktemp(suffix='.db')
        
        # 初始化DataImporter
        self.importer = DataImporter()
        # 修改DataImporter中的数据库路径
        self.importer.db_manager = DatabaseManager(db_path=self.temp_db)
        
        # 创建临时测试CSV文件
        self.test_csv_path = tempfile.mktemp(suffix='.csv')
        self.create_test_csv()
        
        # 创建不支持的文件格式
        self.unsupported_file = tempfile.mktemp(suffix='.txt')
        with open(self.unsupported_file, 'w') as f:
            f.write('测试内容')
    
    def tearDown(self):
        # 删除临时文件
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        
        if os.path.exists(self.unsupported_file):
            os.remove(self.unsupported_file)
    
    def create_test_csv(self):
        """创建测试CSV文件"""
        test_data = {
            '成交日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
            '股票代码': ['000001', '000002', '000001'],
            '股票名称': ['平安银行', '万科A', '平安银行'],
            '买卖': ['买入', '买入', '卖出'],
            '股数': [100, 200, 50],
            '成交价格': [10.0, 20.0, 11.0],
            '成交金额': [1000.0, 4000.0, 550.0],
            '佣金': [5.0, 8.0, 3.0],
            '印花税': [0.0, 0.0, 0.55],
            '成交编号': ['1', '2', '3']
        }
        
        df = pd.DataFrame(test_data)
        df.to_csv(self.test_csv_path, index=False, encoding='utf-8')
    
    def test_is_supported_format(self):
        """测试文件格式检查功能"""
        # 测试支持的格式
        self.assertTrue(self.importer.is_supported_format('test.csv'))
        self.assertTrue(self.importer.is_supported_format('test.xlsx'))
        self.assertTrue(self.importer.is_supported_format('test.xls'))
        
        # 测试不支持的格式
        self.assertFalse(self.importer.is_supported_format('test.txt'))
        self.assertFalse(self.importer.is_supported_format('test.pdf'))
        self.assertFalse(self.importer.is_supported_format('test.docx'))
    
    def test_read_file(self):
        """测试文件读取功能"""
        # 测试读取CSV文件
        df = self.importer.read_file(self.test_csv_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        
        # 测试读取不支持的格式
        with self.assertRaises(ValueError):
            self.importer.read_file(self.unsupported_file)
    
    def test_detect_columns(self):
        """测试列检测功能"""
        df = self.importer.read_file(self.test_csv_path)
        column_mapping = self.importer.detect_columns(df)
        
        # 验证检测到的列映射
        self.assertEqual(column_mapping['trade_date'], '成交日期')
        self.assertEqual(column_mapping['stock_code'], '股票代码')
        self.assertEqual(column_mapping['stock_name'], '股票名称')
        self.assertEqual(column_mapping['trade_type'], '买卖')
        self.assertEqual(column_mapping['quantity'], '股数')
        self.assertEqual(column_mapping['price'], '成交价格')
        self.assertEqual(column_mapping['amount'], '成交金额')
        self.assertEqual(column_mapping['brokerage'], '佣金')
        self.assertEqual(column_mapping['tax'], '印花税')
        self.assertEqual(column_mapping['trade_id'], '成交编号')
    
    def test_clean_trade_data(self):
        """测试数据清洗功能"""
        df = self.importer.read_file(self.test_csv_path)
        column_mapping = self.importer.detect_columns(df)
        cleaned_data = self.importer.clean_trade_data(df, column_mapping)
        
        # 验证清洗后的数据
        self.assertEqual(len(cleaned_data), 3)
        
        # 验证第一条记录
        record1 = cleaned_data[0]
        self.assertEqual(record1['trade_date'], '2024-01-01 00:00:00')
        self.assertEqual(record1['stock_code'], '000001')
        self.assertEqual(record1['stock_name'], '平安银行')
        self.assertEqual(record1['trade_type'], 'BUY')
        self.assertEqual(record1['quantity'], 100)
        self.assertEqual(record1['price'], 10.0)
        self.assertEqual(record1['amount'], 1000.0)
        self.assertEqual(record1['brokerage'], 5.0)
        self.assertEqual(record1['tax'], 0.0)
        self.assertEqual(record1['net_amount'], 1005.0)
        
        # 验证第三条记录（卖出）
        record3 = cleaned_data[2]
        self.assertEqual(record3['trade_type'], 'SELL')
        self.assertEqual(record3['quantity'], 50)
        self.assertEqual(record3['price'], 11.0)
        self.assertEqual(record3['amount'], 550.0)
        self.assertEqual(record3['net_amount'], 546.45)  # 550 - 3 - 0.55 = 546.45
    
    def test_import_data(self):
        """测试数据导入功能"""
        # 初始化数据库
        self.importer.db_manager.init_database()
        
        # 导入数据
        imported_count = self.importer.import_data(self.test_csv_path)
        
        # 验证导入成功
        self.assertEqual(imported_count, 3)
        
        # 验证数据已导入数据库
        trades = self.importer.db_manager.get_all_trades()
        self.assertEqual(len(trades), 3)
        
        # 验证持仓已更新
        positions = self.importer.db_manager.get_current_positions()
        self.assertEqual(len(positions), 2)  # 两支股票的持仓

if __name__ == '__main__':
    unittest.main()
