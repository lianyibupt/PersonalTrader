import os
import json
import asyncio
from datetime import datetime
import cognee
from src.utils.database import DatabaseManager
import logging
import numpy as np
import requests

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
        self.mode = "cognee"  # cognee 或 local 回退模式
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Embedding provider config
        self.embed_provider = None  # "ollama" | "openai"
        self.embed_base_url = None
        self.embed_model = None
        self.embed_api_key = None
        self.embeddings_index_path = os.path.join(self.storage_path, "embeddings_index.json")
        self.embeddings_index = []  # list of {id, vector, text}
        self.use_cognee = True
        
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

    def configure_llm(self, provider, base_url=None, api_key=None):
        if provider == "local":
            os.environ["OPENAI_BASE_URL"] = base_url or "http://127.0.0.1:1234/v1"
            os.environ["OPENAI_API_KEY"] = api_key or "lm-studio"
        else:
            if base_url:
                os.environ["OPENAI_BASE_URL"] = base_url
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.mode = "cognee"

    def configure_cognee(self, enabled: bool):
        self.use_cognee = bool(enabled)

    def configure_embedding(self, provider, base_url, model, api_key=None):
        self.embed_provider = provider
        self.embed_base_url = base_url
        self.embed_model = model
        self.embed_api_key = api_key
        # 清空内存索引，下一次构建时重新生成
        self.embeddings_index = []

    def _get_embedding(self, text):
        if not self.embed_provider or not self.embed_base_url or not self.embed_model:
            raise RuntimeError("Embedding 未配置")
        try:
            if self.embed_provider == "openai":
                url = self.embed_base_url.rstrip("/") + "/embeddings"
                headers = {"Content-Type": "application/json"}
                if self.embed_api_key:
                    headers["Authorization"] = f"Bearer {self.embed_api_key}"
                payload = {"model": self.embed_model, "input": text}
                resp = requests.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return resp.json()["data"][0]["embedding"]
            elif self.embed_provider == "ollama":
                # Ollama default base: http://127.0.0.1:11434
                url = self.embed_base_url.rstrip("/") + "/api/embeddings"
                payload = {"model": self.embed_model, "input": text}
                resp = requests.post(url, json=payload)
                resp.raise_for_status()
                return resp.json().get("embedding")
            else:
                raise RuntimeError("未知的Embedding提供者")
        except Exception as e:
            raise RuntimeError(f"获取Embedding失败: {e}")

    @staticmethod
    def _cosine(a, b):
        a = np.array(a, dtype=np.float32)
        b = np.array(b, dtype=np.float32)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
    
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

            processed_count = 0
            try:
                if self.use_cognee:
                    async def _process_trades():
                        processed = 0
                        for trade in trades:
                            try:
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

                        await cognee.cognify()
                        await cognee.memify()
                        return processed

                    processed_count = asyncio.run(_process_trades())
                else:
                    processed_count = 0
            except Exception as e:
                # 若因 LLM API Key 或远端依赖不可用导致失败，回退到本地模式
                logger.error(f"Cognee 处理失败，回退到本地模式: {e}")
                self.mode = "local"
                processed_count = 0

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
            # 若配置了本地Embedding，则构建向量索引
            if self.embed_provider:
                try:
                    index = []
                    for trade in trades:
                        text = (
                            f"{trade['trade_date']} {trade['trade_type']} {trade['quantity']} "
                            f"{trade['stock_code']} {trade.get('stock_name') or ''} price {trade['price']} amount {trade['amount']}"
                        )
                        vec = self._get_embedding(text)
                        if vec is not None:
                            index.append({"id": trade["id"], "vector": vec, "text": text})
                    # 保存索引
                    os.makedirs(self.storage_path, exist_ok=True)
                    with open(self.embeddings_index_path, "w", encoding="utf-8") as f:
                        json.dump(index, f)
                    self.embeddings_index = index
                    self.mode = "embedding_local"
                    logger.info(f"已构建本地Embedding索引，共 {len(index)} 条")
                except Exception as ie:
                    logger.error(f"构建本地Embedding索引失败: {ie}")
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
            if self.mode == "cognee":
                async def _search():
                    return await cognee.search(
                        query_text=query,
                        query_type=cognee.SearchType.GRAPH_COMPLETION,
                        top_k=limit,
                    )
                results = asyncio.run(_search())
                return results
            elif self.mode == "embedding_local" and self.embeddings_index:
                try:
                    qvec = self._get_embedding(query)
                    scored = []
                    for item in self.embeddings_index:
                        score = self._cosine(qvec, item["vector"])
                        scored.append((score, item["id"]))
                    scored.sort(key=lambda x: -x[0])
                    ids = [sid for _, sid in scored[:limit]]
                    # 映射回交易记录
                    trades = self.db_manager.get_all_trades(limit=10000)
                    by_id = {t['id']: t for t in trades}
                    return [by_id[i] for i in ids if i in by_id]
                except Exception as e:
                    logger.error(f"本地向量检索失败，改用关键词匹配: {e}")
            else:
                # 本地回退：使用简单关键词匹配在交易文本中检索
                trades = self.db_manager.get_all_trades(limit=10000)
                q = query.lower()
                scored = []
                for t in trades:
                    text = (
                        f"{t.get('stock_code','')} {t.get('stock_name','')} "
                        f"{t.get('trade_type','')} {t.get('trade_date','')} "
                        f"{t.get('quantity','')} {t.get('price','')} {t.get('amount','')}"
                    ).lower()
                    score = 0
                    for token in q.split():
                        if token and token in text:
                            score += 1
                    if score > 0:
                        scored.append((score, t))
                scored.sort(key=lambda x: (-x[0], x[1].get('trade_date','')))
                return [s[1] for s in scored[:limit]]
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
