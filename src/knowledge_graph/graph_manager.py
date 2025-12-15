import os
import json
import asyncio
from datetime import datetime
import cognee
from src.utils.database import DatabaseManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphManager:
    def __init__(self, storage_path="data/cognee_storage"):
        self.storage_path = storage_path
        self.db_manager = DatabaseManager()
        # 本地缓存一份用于前端展示的简化图数据
        self.graph_data = {"nodes": [], "edges": []}
        self.initialized = False
        
    def initialize(self):
        """初始化Cognee知识图谱（使用新版cognee API）"""
        try:
            # 新版本 cognee 在导入时会自动初始化本地存储
            os.makedirs(self.storage_path, exist_ok=True)
            self.initialized = True
            logger.info("Cognee知识图谱初始化成功（使用全局 API）")
            return True
        except Exception as e:
            logger.error(f"Cognee知识图谱初始化失败: {str(e)}")
            return False
    
    def build_graph_from_trades(self):
        """从交易数据构建知识图谱

        使用新版 cognee 的全局 add/cognify/memify API，将交易信息写入
        Cognee 的记忆存储，同时在本地构建一个简化的 nodes/edges 结构，
        用于前端展示。
        """
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            # 获取所有交易记录
            trades = self.db_manager.get_all_trades(limit=10000)
            
            if not trades:
                logger.info("没有交易数据可供构建知识图谱")
                return 0
            
            logger.info(f"开始处理 {len(trades)} 条交易记录")

            async def _process_trades():
                processed = 0
                for trade in trades:
                    try:
                        # 用自然语言描述交易，方便后续语义搜索
                        text = (
                            f"交易 {trade['id']}: 在 {trade['trade_date']} "
                            f"{trade['trade_type']} {trade['quantity']} 股 "
                            f"{trade['stock_code']}({trade.get('stock_name') or ''}) "
                            f"价格 {trade['price']} 金额 {trade['amount']}"
                        )
                        await cognee.add(text)
                        processed += 1
                    except Exception as inner_e:
                        logger.error(f"处理交易记录 {trade.get('id')} 失败: {inner_e}")
                        continue

                # 触发认知与记忆构建
                await cognee.cognify()
                await cognee.memify()
                return processed

            processed_count = asyncio.run(_process_trades())

            # 同时构建一个用于前端展示的简化图结构
            nodes = {}
            edges = []

            for trade in trades:
                trade_node_id = f"trade_{trade['id']}"
                stock_node_id = f"stock_{trade['stock_code']}"

                if stock_node_id not in nodes:
                    nodes[stock_node_id] = {
                        "id": stock_node_id,
                        "type": "stock",
                        "stock_code": trade["stock_code"],
                        "stock_name": trade.get("stock_name"),
                    }

                if trade_node_id not in nodes:
                    nodes[trade_node_id] = {
                        "id": trade_node_id,
                        "type": "trade",
                        "trade_id": trade.get("trade_id"),
                        "trade_date": trade["trade_date"],
                        "trade_type": trade["trade_type"],
                        "quantity": trade["quantity"],
                        "price": trade["price"],
                        "amount": trade["amount"],
                    }

                edges.append(
                    {
                        "source": trade_node_id,
                        "target": stock_node_id,
                        "relation": trade["trade_type"],
                    }
                )

            self.graph_data = {"nodes": list(nodes.values()), "edges": edges}

            logger.info(f"知识图谱构建完成，成功处理 {processed_count} 条交易记录")
            return processed_count
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise
    
    def get_graph_data(self):
        """获取知识图谱数据"""
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            # 直接返回本地缓存的简化图结构
            return self.graph_data
        except Exception as e:
            logger.error(f"获取知识图谱数据失败: {str(e)}")
            return None
    
    def query_graph(self, query, limit=10):
        """查询知识图谱"""
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            # 使用新版 cognee 的 search API 进行语义检索
            async def _search():
                return await cognee.search(
                    query_text=query,
                    query_type=cognee.SearchType.GRAPH_COMPLETION,
                    top_k=limit,
                )

            results = asyncio.run(_search())
            return results
        except Exception as e:
            logger.error(f"查询知识图谱失败: {str(e)}")
            return None
    
    def add_trade_to_graph(self, trade_data):
        """添加单条交易记录到知识图谱"""
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            async def _add_one():
                text = json.dumps(trade_data, ensure_ascii=False)
                await cognee.add(text)
                await cognee.cognify()
                await cognee.memify()

            asyncio.run(_add_one())

            logger.info(f"成功将交易记录添加到知识图谱: {trade_data.get('trade_id')}")
            return True
        except Exception as e:
            logger.error(f"添加交易记录到知识图谱失败: {str(e)}")
            return False
    
    def get_stock_relations(self, stock_code):
        """获取特定股票的关系数据"""
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            # 通过语义搜索获取与该股票相关的记忆
            async def _search_stock():
                query_text = f"关于股票 {stock_code} 的所有交易和记忆"
                return await cognee.search(query_text=query_text, top_k=20)

            results = asyncio.run(_search_stock())
            return results
        except Exception as e:
            logger.error(f"获取股票关系数据失败: {str(e)}")
            return None
    
    def clear_graph(self):
        """清空知识图谱数据"""
        if not self.initialized:
            if not self.initialize():
                raise Exception("知识图谱未初始化")
        
        try:
            # 清除 Cognee 记忆（通过 prune API）
            async def _clear():
                await cognee.prune()

            asyncio.run(_clear())
            self.graph_data = {"nodes": [], "edges": []}
            logger.info("知识图谱数据已清空")
            return True
        except Exception as e:
            logger.error(f"清空知识图谱数据失败: {str(e)}")
            return False

# 示例用法
if __name__ == "__main__":
    graph_manager = GraphManager()
    graph_manager.initialize()
    
    # 从交易数据构建知识图谱
    count = graph_manager.build_graph_from_trades()
    print(f"成功处理 {count} 条交易记录")
    
    # 获取图数据
    graph_data = graph_manager.get_graph_data()
    print(f"知识图谱包含 {len(graph_data.get('nodes', []))} 个节点和 {len(graph_data.get('edges', []))} 条边")
