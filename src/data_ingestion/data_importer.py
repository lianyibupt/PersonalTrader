import pandas as pd
import os
import re
import logging
from datetime import datetime
from src.utils.database import DatabaseManager

class DataImporter:
    def __init__(self):
        self.db_manager = DatabaseManager()
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.supported_formats = ['.csv', '.xlsx', '.xls']

    def is_supported_format(self, file_path):
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats

    def read_file(self, file_input):
        """读取支持的文件格式并返回DataFrame"""
        # 检查输入类型
        if hasattr(file_input, 'name'):  # Streamlit UploadedFile对象
            file_name = file_input.name
            ext = os.path.splitext(file_name)[1].lower()
            file_obj = file_input
        else:  # 文件路径字符串
            if not self.is_supported_format(file_input):
                raise ValueError(f"不支持的文件格式: {file_input}")
            ext = os.path.splitext(file_input)[1].lower()
            file_obj = file_input
        
        try:
            if ext == '.csv':
                # 尝试不同的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_obj, encoding=encoding)
                        return df
                    except UnicodeDecodeError:
                        continue
                raise ValueError(f"无法解码CSV文件")
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_obj)
                return df
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")

    def detect_columns(self, df):
        """自动检测列映射关系"""
        columns = df.columns.str.lower()
        column_mapping = {
            'trade_date': None,  # 下单时间
            'stock_code': None,  # 代码
            'stock_name': None,  # 名称
            'trade_type': None,  # 方向
            'quantity': None,  # 订单数量
            'price': None,  # 订单价格
            'amount': None,  # 订单金额
            'order_status': None,  # 交易状态
            'filled_quantity': None,  # 已成交
            'order_type': None,  # 订单类型
            'duration': None,  # 期限
            'time_slot': None,  # 时段
            'currency': None,  # 币种
            'market': None,  # 市场
            'brokerage': None,  # 佣金
            'tax': None,  # 税费
            'net_amount': None,  # 净额
            'trade_id': None  # 交易ID
        }

        # 交易日期检测
        date_patterns = ['date', 'trade_date', '成交日期', '交易日期', '日期', '下单时间', '成交时间']
        for col in columns:
            if any(pattern in col for pattern in date_patterns):
                column_mapping['trade_date'] = df.columns[columns.get_loc(col)]
                break

        # 股票代码检测
        code_patterns = ['code', 'stock_code', '股票代码', '代码', '证券代码']
        for col in columns:
            if any(pattern in col for pattern in code_patterns):
                column_mapping['stock_code'] = df.columns[columns.get_loc(col)]
                break

        # 股票名称检测
        name_patterns = ['name', 'stock_name', '股票名称', '名称', '证券名称']
        for col in columns:
            if any(pattern in col for pattern in name_patterns):
                column_mapping['stock_name'] = df.columns[columns.get_loc(col)]
                break

        # 交易类型检测
        type_patterns = ['type', 'trade_type', '买卖', '交易类型', '操作', '方向', '交易方向']
        for col in columns:
            if any(pattern in col for pattern in type_patterns):
                column_mapping['trade_type'] = df.columns[columns.get_loc(col)]
                break

        # 数量检测
        quantity_patterns = ['quantity', '股数', '数量', '成交数量', '成交量', '订单数量']
        for col in columns:
            if any(pattern in col for pattern in quantity_patterns):
                column_mapping['quantity'] = df.columns[columns.get_loc(col)]
                break

        # 价格检测
        price_patterns = ['price', '价格', '成交价格', '成交价', '订单价格']
        for col in columns:
            if any(pattern in col for pattern in price_patterns):
                column_mapping['price'] = df.columns[columns.get_loc(col)]
                break

        # 金额检测
        amount_patterns = ['amount', '金额', '成交金额', '成交额', '订单金额']
        for col in columns:
            if any(pattern in col for pattern in amount_patterns):
                column_mapping['amount'] = df.columns[columns.get_loc(col)]
                break

        # 佣金检测
        brokerage_patterns = ['brokerage', '佣金', '手续费', '费用']
        for col in columns:
            if any(pattern in col for pattern in brokerage_patterns):
                column_mapping['brokerage'] = df.columns[columns.get_loc(col)]
                break

        # 税费检测
        tax_patterns = ['tax', '税', '印花税', '过户费']
        for col in columns:
            if any(pattern in col for pattern in tax_patterns):
                column_mapping['tax'] = df.columns[columns.get_loc(col)]
                break

        # 净额检测
        net_patterns = ['net', '净额', '净金额', '实际金额']
        for col in columns:
            if any(pattern in col for pattern in net_patterns):
                column_mapping['net_amount'] = df.columns[columns.get_loc(col)]
                break

        # 交易ID检测
        id_patterns = ['id', 'trade_id', '成交编号', '流水号', '订单号']
        for col in columns:
            if any(pattern in col for pattern in id_patterns):
                column_mapping['trade_id'] = df.columns[columns.get_loc(col)]
                break

        # 交易状态检测
        status_patterns = ['order_status', '交易状态', '状态']
        for col in columns:
            if any(pattern in col for pattern in status_patterns):
                column_mapping['order_status'] = df.columns[columns.get_loc(col)]
                break

        # 已成交数量检测
        filled_patterns = ['filled_quantity', '已成交', '成交数量']
        for col in columns:
            if any(pattern in col for pattern in filled_patterns):
                column_mapping['filled_quantity'] = df.columns[columns.get_loc(col)]
                break

        # 订单类型检测
        order_type_patterns = ['order_type', '订单类型', '类型']
        for col in columns:
            if any(pattern in col for pattern in order_type_patterns):
                column_mapping['order_type'] = df.columns[columns.get_loc(col)]
                break

        # 期限检测
        duration_patterns = ['duration', '期限', '有效期']
        for col in columns:
            if any(pattern in col for pattern in duration_patterns):
                column_mapping['duration'] = df.columns[columns.get_loc(col)]
                break

        # 时段检测
        time_slot_patterns = ['time_slot', '时段', '时间范围']
        for col in columns:
            if any(pattern in col for pattern in time_slot_patterns):
                column_mapping['time_slot'] = df.columns[columns.get_loc(col)]
                break

        # 币种检测
        currency_patterns = ['currency', '币种', '货币']
        for col in columns:
            if any(pattern in col for pattern in currency_patterns):
                column_mapping['currency'] = df.columns[columns.get_loc(col)]
                break

        # 市场检测
        market_patterns = ['market', '市场', '交易所']
        for col in columns:
            if any(pattern in col for pattern in market_patterns):
                column_mapping['market'] = df.columns[columns.get_loc(col)]
                break

        return column_mapping

    def clean_trade_data(self, df, column_mapping):
        cleaned_data = []

        for _, row in df.iterrows():
            trade_record = {}

            try:
                date_col = column_mapping['trade_date']
                if pd.notna(row[date_col]):
                    if isinstance(row[date_col], datetime):
                        trade_record['trade_date'] = row[date_col].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        date_str = str(row[date_col]).strip()
                        date_str = re.sub(r'（.*?）', '', date_str)
                        date_str = re.sub(r'\(.*?\)', '', date_str).strip()
                        date_formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d %H:%M',
                            '%Y-%m-%d',
                            '%Y/%m/%d %H:%M:%S',
                            '%Y/%m/%d %H:%M',
                            '%Y/%m/%d',
                            '%d/%m/%Y',
                            '%d-%m-%Y'
                        ]
                        parsed = False
                        for fmt in date_formats:
                            try:
                                dt = datetime.strptime(date_str, fmt)
                                trade_record['trade_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                                parsed = True
                                break
                            except ValueError:
                                continue
                        if not parsed:
                            try:
                                timestamp = float(date_str)
                                dt = datetime.fromtimestamp(timestamp)
                                trade_record['trade_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                                parsed = True
                            except:
                                continue
                if 'trade_date' not in trade_record:
                    continue
            except:
                continue

            # 处理股票代码
            try:
                code_col = column_mapping['stock_code']
                if pd.notna(row[code_col]):
                    # 确保股票代码作为字符串处理，保留前导零
                    code_value = row[code_col]
                    if isinstance(code_value, (int, float)):
                        # 如果是数字，转换为字符串并补零到6位（A股代码格式）
                        trade_record['stock_code'] = f"{int(code_value):06d}"
                    else:
                        trade_record['stock_code'] = str(code_value).strip()
                    # 移除可能的交易所后缀（如.SH, .SZ）
                    trade_record['stock_code'] = re.sub(r'\.(SH|SZ|HK|US)$', '', trade_record['stock_code'])
                else:
                    continue
            except:
                continue

            # 处理股票名称
            try:
                name_col = column_mapping['stock_name']
                if name_col and pd.notna(row[name_col]):
                    trade_record['stock_name'] = str(row[name_col]).strip()
            except:
                pass

            # 处理交易类型
            try:
                type_col = column_mapping['trade_type']
                if type_col and pd.notna(row[type_col]):
                    trade_type = str(row[type_col]).strip().upper()
                    # 映射中文买卖类型
                    if trade_type in ['买入', '买', 'BUY', 'B', '1']:
                        trade_record['trade_type'] = 'BUY'
                    elif trade_type in ['卖出', '卖', 'SELL', 'S', '2']:
                        trade_record['trade_type'] = 'SELL'
                    else:
                        continue
                else:
                    continue
            except:
                continue

            # 处理数量
            try:
                qty_col = column_mapping['quantity']
                if qty_col and pd.notna(row[qty_col]):
                    trade_record['quantity'] = int(float(str(row[qty_col]).replace(',', '')))
                else:
                    continue
            except:
                continue

            # 处理价格
            try:
                price_col = column_mapping['price']
                if price_col and pd.notna(row[price_col]):
                    trade_record['price'] = float(str(row[price_col]).replace(',', ''))
                else:
                    continue
            except:
                continue

            # 处理金额
            try:
                amount_col = column_mapping['amount']
                if amount_col and pd.notna(row[amount_col]):
                    trade_record['amount'] = float(str(row[amount_col]).replace(',', ''))
                else:
                    # 如果没有金额字段，计算金额
                    trade_record['amount'] = trade_record['quantity'] * trade_record['price']
            except:
                trade_record['amount'] = trade_record['quantity'] * trade_record['price']

            # 处理佣金
            try:
                brokerage_col = column_mapping['brokerage']
                if brokerage_col and pd.notna(row[brokerage_col]):
                    trade_record['brokerage'] = float(str(row[brokerage_col]).replace(',', ''))
                else:
                    trade_record['brokerage'] = 0.0
            except:
                trade_record['brokerage'] = 0.0

            # 处理税费
            try:
                tax_col = column_mapping['tax']
                if tax_col and pd.notna(row[tax_col]):
                    trade_record['tax'] = float(str(row[tax_col]).replace(',', ''))
                else:
                    trade_record['tax'] = 0.0
            except:
                trade_record['tax'] = 0.0

            # 处理净额
            try:
                net_col = column_mapping['net_amount']
                if net_col and pd.notna(row[net_col]):
                    trade_record['net_amount'] = float(str(row[net_col]).replace(',', ''))
                else:
                    # 计算净额
                    if trade_record['trade_type'] == 'BUY':
                        trade_record['net_amount'] = trade_record['amount'] + trade_record['brokerage'] + trade_record['tax']
                    else:
                        trade_record['net_amount'] = trade_record['amount'] - trade_record['brokerage'] - trade_record['tax']
            except:
                # 计算净额
                if trade_record['trade_type'] == 'BUY':
                    trade_record['net_amount'] = trade_record['amount'] + trade_record['brokerage'] + trade_record['tax']
                else:
                    trade_record['net_amount'] = trade_record['amount'] - trade_record['brokerage'] - trade_record['tax']

            # 处理交易ID
            try:
                id_col = column_mapping['trade_id']
                if id_col and pd.notna(row[id_col]):
                    trade_record['trade_id'] = str(row[id_col]).strip()
            except:
                pass

            # 处理交易状态
            try:
                status_col = column_mapping['order_status']
                if status_col and pd.notna(row[status_col]):
                    trade_record['order_status'] = str(row[status_col]).strip()
            except:
                pass

            # 处理已成交数量
            try:
                filled_col = column_mapping['filled_quantity']
                if filled_col and pd.notna(row[filled_col]):
                    trade_record['filled_quantity'] = int(float(str(row[filled_col]).replace(',', '')))
            except:
                pass

            # 处理订单类型
            try:
                type_col = column_mapping['order_type']
                if type_col and pd.notna(row[type_col]):
                    trade_record['order_type'] = str(row[type_col]).strip()
            except:
                pass

            # 处理期限
            try:
                duration_col = column_mapping['duration']
                if duration_col and pd.notna(row[duration_col]):
                    trade_record['duration'] = str(row[duration_col]).strip()
            except:
                pass

            # 处理时段
            try:
                time_slot_col = column_mapping['time_slot']
                if time_slot_col and pd.notna(row[time_slot_col]):
                    trade_record['time_slot'] = str(row[time_slot_col]).strip()
            except:
                pass

            # 处理币种
            try:
                currency_col = column_mapping['currency']
                if currency_col and pd.notna(row[currency_col]):
                    trade_record['currency'] = str(row[currency_col]).strip()
            except:
                pass

            # 处理市场
            try:
                market_col = column_mapping['market']
                if market_col and pd.notna(row[market_col]):
                    trade_record['market'] = str(row[market_col]).strip()
            except:
                pass

            # 确保所有必填字段都有值
            required_fields = ['trade_date', 'stock_code', 'trade_type', 'quantity', 'price', 'amount', 'net_amount']
            if all(field in trade_record for field in required_fields):
                cleaned_data.append(trade_record)

        return cleaned_data

    def import_data(self, file_path, column_mapping=None):
        df = self.read_file(file_path)
        try:
            total_rows = len(df)
        except Exception:
            total_rows = -1
        self.logger.info(f"开始导入文件: {file_path}, 行数: {total_rows}")

        if not column_mapping:
            column_mapping = self.detect_columns(df)
        self.logger.info(f"列映射结果: {column_mapping}")

        if not column_mapping['trade_date'] or not column_mapping['stock_code'] or not column_mapping['trade_type']:
            raise Exception("无法检测到必要的字段映射关系")

        cleaned_data = self.clean_trade_data(df, column_mapping)

        self.logger.info(f"清洗后有效记录数: {len(cleaned_data)}")

        if not cleaned_data:
            try:
                sample_dates = df[column_mapping['trade_date']].head().tolist()
            except Exception:
                sample_dates = []
            self.logger.warning(f"没有可导入的有效数据, 示例日期值: {sample_dates}")
            raise Exception("没有可导入的有效数据")

        # 导入到数据库
        imported_count = 0
        for trade_record in cleaned_data:
            result = self.db_manager.insert_trade(trade_record)
            if result:
                imported_count += 1

        # 更新持仓
        self.update_positions()

        return imported_count

    def update_positions(self):
        """根据交易记录更新持仓信息"""
        # 获取所有交易记录并按日期排序
        trades = self.db_manager.get_all_trades(limit=10000)
        
        # 按股票代码分组
        positions = {}
        
        for trade in trades:
            stock_code = trade['stock_code']
            stock_name = trade['stock_name']
            trade_type = trade['trade_type']
            quantity = trade['quantity']
            price = trade['price']
            amount = trade['amount']
            
            if stock_code not in positions:
                positions[stock_code] = {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'quantity': 0,
                    'total_cost': 0,
                    'avg_cost': 0
                }
            
            if trade_type == 'BUY':
                positions[stock_code]['quantity'] += quantity
                positions[stock_code]['total_cost'] += amount
            else:  # SELL
                if positions[stock_code]['quantity'] >= quantity:
                    # 计算卖出部分的成本
                    sell_cost = (positions[stock_code]['total_cost'] / positions[stock_code]['quantity']) * quantity
                    positions[stock_code]['quantity'] -= quantity
                    positions[stock_code]['total_cost'] -= sell_cost
            
            # 更新平均成本
            if positions[stock_code]['quantity'] > 0:
                positions[stock_code]['avg_cost'] = positions[stock_code]['total_cost'] / positions[stock_code]['quantity']
            else:
                positions[stock_code]['avg_cost'] = 0
        
        # 更新持仓表
        for stock_code, pos_data in positions.items():
            if pos_data['quantity'] > 0:
                position_record = {
                    'stock_code': pos_data['stock_code'],
                    'stock_name': pos_data['stock_name'],
                    'quantity': pos_data['quantity'],
                    'avg_cost': pos_data['avg_cost'],
                    'current_price': pos_data['avg_cost'],  # 暂时使用平均成本作为当前价格
                    'market_value': pos_data['avg_cost'] * pos_data['quantity'],
                    'profit': 0,  # 暂时为0
                    'profit_rate': 0  # 暂时为0
                }
                self.db_manager.update_position(position_record)

# 使用示例
if __name__ == "__main__":
    importer = DataImporter()
    print("数据导入模块初始化完成")
