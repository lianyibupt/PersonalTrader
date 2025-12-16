import sqlite3
import os
import shutil
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data/trading.db"):
        # 创建data目录（如果不存在）
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接到SQLite数据库"""
        self.conn = sqlite3.connect(self.db_path)
        # 配置cursor返回字典格式
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def execute(self, query, params=None):
        """执行SQL查询"""
        if not self.cursor:
            self.connect()
        if params:
            return self.cursor.execute(query, params)
        else:
            return self.cursor.execute(query)

    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()

    def init_database(self):
        """初始化数据库和表结构"""
        self.connect()
        
        # 创建交易记录表
        self.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT NOT NULL, -- 下单时间
            stock_code TEXT NOT NULL, -- 代码
            stock_name TEXT, -- 名称
            trade_type TEXT NOT NULL, -- 'BUY' or 'SELL'（方向）
            quantity INTEGER NOT NULL, -- 订单数量
            price REAL NOT NULL, -- 订单价格
            amount REAL NOT NULL, -- 订单金额
            order_status TEXT, -- 交易状态
            filled_quantity INTEGER, -- 已成交
            order_type TEXT, -- 订单类型
            duration TEXT, -- 期限
            time_slot TEXT, -- 时段
            currency TEXT, -- 币种
            market TEXT, -- 市场
            brokerage REAL, -- 佣金
            tax REAL, -- 税费
            net_amount REAL NOT NULL, -- 净额
            trade_id TEXT UNIQUE, -- 交易ID
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建持仓表
        self.execute('''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_code TEXT NOT NULL,
            stock_name TEXT,
            quantity INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            current_price REAL,
            market_value REAL,
            profit REAL,
            profit_rate REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(stock_code)
        )
        ''')

        # 创建市场数据表
        self.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            turnover REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, stock_code)
        )
        ''')

        # 创建日志表
        self.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT,
            details TEXT
        )
        ''')

        # 创建聊天历史表
        self.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL, -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        ''')

        self.commit()
        self.migrate_tables()
        self.disconnect()

    def backup_database(self):
        if os.path.exists(self.db_path):
            bak_path = self.db_path + ".bak"
            shutil.copy2(self.db_path, bak_path)
            return bak_path
        return None

    def get_table_columns(self, table_name):
        self.connect()
        try:
            cur = self.execute(f"PRAGMA table_info({table_name})")
            cols = [row[1] for row in cur.fetchall()]
            return set(cols)
        finally:
            self.disconnect()

    def migrate_tables(self):
        self.backup_database()
        existing = self.get_table_columns('trades')
        add_sql = []
        if 'order_status' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN order_status TEXT")
        if 'filled_quantity' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN filled_quantity INTEGER")
        if 'order_type' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN order_type TEXT")
        if 'duration' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN duration TEXT")
        if 'time_slot' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN time_slot TEXT")
        if 'currency' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN currency TEXT")
        if 'market' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN market TEXT")
        if 'brokerage' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN brokerage REAL DEFAULT 0")
        if 'tax' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN tax REAL DEFAULT 0")
        if 'net_amount' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN net_amount REAL NOT NULL DEFAULT 0")
        if 'trade_id' not in existing:
            add_sql.append("ALTER TABLE trades ADD COLUMN trade_id TEXT")
        self.connect()
        try:
            for sql in add_sql:
                self.execute(sql)
            self.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_trades_trade_id ON trades(trade_id)")
            self.commit()
        finally:
            self.disconnect()

    def insert_trade(self, trade_data):
        self.connect()
        try:
            cols = self.get_table_columns('trades')
            data = dict(trade_data)
            if not data.get('net_amount'):
                amt = float(data.get('amount') or 0)
                brk = float(data.get('brokerage') or 0)
                tax = float(data.get('tax') or 0)
                t = data.get('trade_type')
                if t == 'BUY':
                    data['net_amount'] = amt + brk + tax
                elif t == 'SELL':
                    data['net_amount'] = amt - brk - tax
                else:
                    data['net_amount'] = amt
            insert_cols = [k for k in data.keys() if k in cols]
            placeholders = ", ".join(["?"] * len(insert_cols))
            col_list = ", ".join(insert_cols)
            values = [data.get(k) for k in insert_cols]
            self.execute(f"INSERT INTO trades ({col_list}) VALUES ({placeholders})", values)
            self.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"交易记录插入失败: {e}")
            return False
        finally:
            self.disconnect()

    def update_position(self, position_data):
        """更新或插入持仓记录"""
        self.connect()
        try:
            self.execute('''
            INSERT INTO positions (stock_code, stock_name, quantity, avg_cost, current_price, market_value, profit, profit_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code) DO UPDATE SET
                stock_name=excluded.stock_name,
                quantity=excluded.quantity,
                avg_cost=excluded.avg_cost,
                current_price=excluded.current_price,
                market_value=excluded.market_value,
                profit=excluded.profit,
                profit_rate=excluded.profit_rate,
                updated_at=CURRENT_TIMESTAMP
            ''', (position_data.get('stock_code'), position_data.get('stock_name'), position_data.get('quantity'),
                  position_data.get('avg_cost'), position_data.get('current_price'), position_data.get('market_value'),
                  position_data.get('profit'), position_data.get('profit_rate')))
            self.commit()
            return True
        except Exception as e:
            print(f"持仓更新失败: {e}")
            return False
        finally:
            self.disconnect()

    def add_log(self, level, message, source=None, details=None):
        """添加日志记录"""
        self.connect()
        try:
            self.execute('''
            INSERT INTO logs (level, message, source, details)
            VALUES (?, ?, ?, ?)
            ''', (level, message, source, details))
            self.commit()
            return True
        except Exception as e:
            print(f"日志添加失败: {e}")
            return False
        finally:
            self.disconnect()

    def add_chat_message(self, session_id, role, content, metadata=None):
        """添加聊天记录"""
        self.connect()
        try:
            self.execute('''
            INSERT INTO chat_history (session_id, role, content, metadata)
            VALUES (?, ?, ?, ?)
            ''', (session_id, role, content, metadata))
            self.commit()
            return True
        except Exception as e:
            print(f"聊天记录添加失败: {e}")
            return False
        finally:
            self.disconnect()

    def get_chat_history(self, session_id, limit=50):
        """获取聊天历史"""
        self.connect()
        try:
            self.execute('''
            SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
            ''', (session_id, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"获取聊天历史失败: {e}")
            return []
        finally:
            self.disconnect()

    def get_all_trades(self, limit=1000):
        """获取所有交易记录"""
        self.connect()
        try:
            self.execute('''
            SELECT * FROM trades ORDER BY trade_date DESC LIMIT ?
            ''', (limit,))
            # 将结果转换为字典列表
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"获取交易记录失败: {e}")
            return []
        finally:
            self.disconnect()

    def get_trades_by_stock(self, stock_code, limit=100):
        """获取指定股票的交易记录"""
        self.connect()
        try:
            self.execute('''
            SELECT * FROM trades WHERE stock_code = ? ORDER BY trade_date DESC LIMIT ?
            ''', (stock_code, limit))
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"获取股票交易记录失败: {e}")
            return []
        finally:
            self.disconnect()

    def get_current_positions(self):
        """获取当前持仓"""
        self.connect()
        try:
            self.execute('''
            SELECT * FROM positions WHERE quantity > 0 ORDER BY stock_code
            ''')
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"获取持仓失败: {e}")
            return []
        finally:
            self.disconnect()

# 初始化数据库示例
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.init_database()
    print("数据库初始化完成！")
