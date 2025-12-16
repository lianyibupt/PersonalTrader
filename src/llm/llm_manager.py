import requests
import json
import logging
import os
from src.utils.database import DatabaseManager
from src.knowledge_graph.graph_manager import GraphManager

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self, model="qwen/qwen3-vl-4b", api_url=None):
        base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_url = api_url or f"{base_url}/chat/completions"
        self.db_manager = DatabaseManager()
        self.graph_manager = GraphManager()
        
    def generate_response(self, prompt, chat_history=None):
        """生成LLM响应"""
        try:
            # 构建消息历史
            messages = []
            
            if chat_history:
                for message in chat_history:
                    messages.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
            
            # 添加当前用户消息
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # 调用LM Studio的OpenAI兼容API
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"LLM生成响应失败: {str(e)}")
            return f"生成响应时发生错误: {str(e)}"
    
    def text_to_sql(self, natural_language_query):
        """将自然语言查询转换为SQL"""
        try:
            # 构建提示词
            prompt = f"""
            你是一个专业的SQL查询生成器。请将以下自然语言查询转换为SQL语句，只输出SQL语句，不要添加任何解释或说明。
            
            数据库表结构：
            trades表包含以下字段：
            - id: 交易ID（整数）
            - trade_date: 交易日期（文本，格式：YYYY-MM-DD HH:MM:SS）
            - stock_code: 股票代码（文本）
            - stock_name: 股票名称（文本）
            - trade_type: 交易类型（文本，'BUY'或'SELL'）
            - quantity: 交易数量（整数）
            - price: 交易价格（实数）
            - amount: 交易金额（实数）
            - brokerage: 佣金（实数）
            - tax: 税费（实数）
            - net_amount: 净额（实数）
            - trade_id: 交易编号（文本）
            - created_at: 创建时间（文本）
            
            positions表包含以下字段：
            - id: 持仓ID（整数）
            - stock_code: 股票代码（文本）
            - stock_name: 股票名称（文本）
            - quantity: 持仓数量（整数）
            - avg_cost: 平均成本（实数）
            - current_price: 当前价格（实数）
            - market_value: 市值（实数）
            - profit: 利润（实数）
            - profit_rate: 利润率（实数）
            - updated_at: 更新时间（文本）
            
            请确保SQL语句正确，并且只返回用户需要的字段。
            
            自然语言查询：{natural_language_query}
            """
            
            # 使用generate_response方法生成SQL
            sql_query = self.generate_response(prompt)
            
            # 清理SQL查询，移除可能的标记
            if sql_query.startswith("```sql"):
                sql_query = sql_query[7:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            logger.info(f"生成的SQL查询: {sql_query}")
            
            return sql_query
            
        except Exception as e:
            logger.error(f"文本到SQL转换失败: {str(e)}")
            return None
    
    def query_with_text_to_sql(self, natural_language_query):
        """使用文本到SQL功能查询数据库"""
        try:
            # 转换为SQL
            sql_query = self.text_to_sql(natural_language_query)
            if not sql_query:
                return "无法生成有效的SQL查询"
            
            # 执行SQL查询
            self.db_manager.connect()
            results = self.db_manager.execute(sql_query).fetchall()
            self.db_manager.disconnect()
            
            # 转换结果为可读格式
            if not results:
                return "查询结果为空"
            
            # 转换为列表字典格式
            result_list = []
            for row in results:
                result_list.append(dict(row))
            
            # 将结果转换为自然语言
            return self.format_query_results(natural_language_query, result_list)
            
        except Exception as e:
            logger.error(f"执行文本到SQL查询失败: {str(e)}")
            return f"查询时发生错误: {str(e)}"
    
    def format_query_results(self, original_query, results):
        """将查询结果格式化为自然语言"""
        try:
            # 构建提示词
            prompt = f"""
            你是一个数据分析助手，请将以下数据库查询结果转换为自然语言回答，回答要简洁明了，直接回答用户的问题。
            
            用户的原始问题：{original_query}
            
            查询结果：
            {json.dumps(results, ensure_ascii=False, indent=2)}
            
            请用自然语言总结查询结果，直接回答用户的问题，不要添加任何额外的解释或说明。
            """
            
            # 使用generate_response方法生成自然语言回答
            return self.generate_response(prompt)
            
        except Exception as e:
            logger.error(f"格式化查询结果失败: {str(e)}")
            # 直接返回原始结果
            return json.dumps(results, ensure_ascii=False, indent=2)
    
    def get_enhanced_response(self, user_query, chat_history=None):
        """获取增强的响应，结合知识图谱和数据库"""
        try:
            # 1. 首先从知识图谱获取相关信息
            graph_results = self.graph_manager.query_graph(user_query)
            graph_info = """
            从知识图谱获取的相关信息：
            """
            if graph_results:
                graph_info += json.dumps(graph_results, ensure_ascii=False, indent=2)
            else:
                graph_info += "无相关信息"
            
            # 2. 检查是否需要查询数据库
            if any(keyword in user_query.lower() for keyword in ["查询", "统计", "有多少", "多少钱", "数量", "成本", "利润"]):
                db_results = self.query_with_text_to_sql(user_query)
                db_info = f"""
                
                从数据库获取的相关信息：
                {db_results}
                """
            else:
                db_info = ""
            
            # 3. 构建增强提示词
            enhanced_prompt = f"""
            你是一个专业的股票交易分析助手，请基于以下信息回答用户的问题：
            
            {graph_info}
            {db_info}
            
            用户的问题：{user_query}
            
            请结合上述信息，给出专业、准确的回答，回答要简洁明了，直接回答用户的问题。
            """
            
            # 4. 生成响应
            return self.generate_response(enhanced_prompt, chat_history)
            
        except Exception as e:
            logger.error(f"获取增强响应失败: {str(e)}")
            # 回退到普通响应
            return self.generate_response(user_query, chat_history)

# 示例用法
if __name__ == "__main__":
    llm_manager = LLMManager()
    
    # 测试文本到SQL功能
    sql_query = llm_manager.text_to_sql("最近10笔交易是什么？")
    print(f"生成的SQL: {sql_query}")
    
    # 测试数据库查询
    results = llm_manager.query_with_text_to_sql("最近10笔交易是什么？")
    print(f"查询结果: {results}")
    
    # 测试增强响应
    response = llm_manager.get_enhanced_response("我最近交易了哪些股票？")
    print(f"增强响应: {response}")
