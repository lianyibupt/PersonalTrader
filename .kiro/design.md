# 📐 本地化个人交易记忆系统 (MyTradeMind) 系统设计文档

## 1. 系统架构图与说明

### 1.1 整体架构概览

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                               前端层 (Web UI)                                  │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐ │
│ │    交易数据可视化       │ │    对话交互界面         │ │    知识图谱可视化   │ │
│ │    (Streamlit)          │ │    (Streamlit)         │ │    (Cognee Viz)     │ │
│ └─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────────┐
│                               应用层 (Application Layer)                       │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐ │
│ │    数据导入模块         │ │    对话管理模块         │ │    图谱管理模块     │ │
│ │    (Data Ingestion)     │ │    (Chat Manager)       │ │    (Graph Manager)  │ │
│ └─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────────┐
│                               核心服务层 (Core Service Layer)                  │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐ │
│ │    本地LLM服务          │ │    知识图谱服务         │ │    数据处理服务     │ │
│ │    (Ollama)             │ │    (Cognee)            │ │    (Data Processor) │ │
│ └─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘ │
└─────────────────────────────────────┬───────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────────┐
│                               数据存储层 (Data Storage Layer)                  │
│ ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐ │
│ │    交易数据库           │ │    知识图谱存储         │ │    对话历史存储     │ │
│ │    (SQLite)             │ │    (Cognee DB)          │ │    (SQLite)         │ │
│ └─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 架构说明

1. **前端层**：使用Streamlit构建交互式Web界面，包含三个主要模块：
   - 交易数据可视化：展示持仓情况、净值曲线等
   - 对话交互界面：提供类似ChatGPT的对话功能
   - 知识图谱可视化：展示Cognee生成的交互式图谱

2. **应用层**：负责处理业务逻辑，连接前端与核心服务：
   - 数据导入模块：处理用户上传的交割单和文档
   - 对话管理模块：管理对话历史和LLM交互
   - 图谱管理模块：管理知识图谱的构建和检索

3. **核心服务层**：系统的核心功能实现：
   - 本地LLM服务：通过Ollama调用本地大语言模型
   - 知识图谱服务：使用Cognee构建和管理知识图谱
   - 数据处理服务：清洗、标准化和分析交易数据

4. **数据存储层**：所有数据本地存储，确保隐私安全：
   - 交易数据库：使用SQLite存储交易记录和行情数据
   - 知识图谱存储：Cognee自带的本地存储
   - 对话历史存储：使用SQLite存储对话历史

## 2. 核心组件设计

### 2.1 数据导入模块 (Data Ingestion Module)

#### 2.1.1 功能与职责
- 处理用户上传的交易记录（CSV/Excel）
- 处理用户上传的策略文档（PDF/Markdown/TXT）
- 提供情绪/日志文本输入界面
- 清洗、标准化和验证数据
- 将数据存储到本地数据库和知识图谱

#### 2.1.2 内部结构
```
┌─────────────────────────────────────────────────────────────────┐
│                    数据导入模块 (DataIngestion)                │
│ ┌────────────────┐ ┌────────────────┐ ┌─────────────────────┐ │
│ │  交割单导入器  │ │  文档导入器    │ │  情绪/日志输入处理器  │ │
│ │ (TradeImporter)│ │(DocumentImporter)│ (LogProcessor)       │ │
│ └────────────────┘ └────────────────┘ └─────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │                        数据验证器                          │ │
│ │                    (DataValidator)                        │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │                        数据标准化器                        │ │
│ │                    (DataNormalizer)                       │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 知识图谱服务 (Knowledge Graph Service)

#### 2.2.1 功能与职责
- 使用Cognee构建和管理知识图谱
- 从文本数据中抽取实体和关系
- 支持图谱查询和可视化
- 为LLM提供图谱增强检索能力

#### 2.2.2 实体与关系定义

**实体类型 (Nodes)**：
- 交易事件 (TradeEvent)：包含交易ID、股票代码、交易时间、交易类型等属性
- 情绪 (Emotion)：包含情绪类型（贪婪/恐惧/焦虑）、强度等属性
- 策略 (Strategy)：包含策略名称、策略描述等属性
- 市场观点 (MarketView)：包含观点类型（看多/看空）、依据等属性
- 股票 (Stock)：包含股票代码、名称、所属板块等属性

**关系类型 (Edges)**：
- 执行于 (EXECUTED_ON)：情绪 -> 交易事件
- 源于 (STEMS_FROM)：交易事件 -> 情绪
- 导致 (LEADS_TO)：交易事件 -> 结果
- 不符合 (VIOLATES)：交易事件 -> 策略
- 锚定 (ANCHORED_TO)：交易事件 -> 策略
- 表达 (EXPRESSES)：交易事件 -> 市场观点

#### 2.2.3 图谱构建流程
```
1. 用户输入情绪/日志文本或上传策略文档
2. 文本被送入Cognee的实体与关系抽取器
3. 使用本地LLM（Ollama）识别文本中的实体和关系
4. 实体和关系被存储到知识图谱中
5. 图谱被优化和索引以提高查询效率
```

### 2.3 对话管理模块 (Chat Manager)

#### 2.3.1 功能与职责
- 管理用户与系统的对话历史
- 处理用户查询并生成响应
- 实现Text-to-SQL功能
- 集成图谱增强检索
- 调用本地LLM生成回复

#### 2.3.2 对话处理流程
```
1. 用户在Web界面输入查询
2. 对话管理模块接收查询
3. 分析查询类型（数据查询/策略咨询/情绪分析）
4. 如需数据查询，调用Text-to-SQL模块生成SQL查询
5. 执行SQL查询获取结果
6. 如需图谱上下文，从Cognee中检索相关实体和关系
7. 将查询、数据结果和图谱上下文组合为Prompt
8. 调用本地LLM（Ollama）生成回复
9. 存储对话历史到SQLite数据库
10. 返回回复给用户
```

### 2.4 数据处理服务 (Data Processor)

#### 2.4.1 功能与职责
- 清洗和标准化交易数据
- 计算交易指标（收益率、胜率、最大回撤等）
- 分析交易模式和行为
- 生成交易报告和统计信息
- 与行情数据接口集成

#### 2.4.2 核心算法
- 交易数据清洗算法：处理缺失值、异常值和重复值
- 交易指标计算：收益率计算、胜率计算、最大回撤计算等
- 模式识别算法：识别情绪与交易结果的关联模式

## 3. 数据模型与流程

### 3.1 数据库模型 (SQLite)

#### 3.1.1 交易记录表 (trades)
```sql
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    trade_type TEXT NOT NULL, -- 'BUY' or 'SELL'
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    amount REAL NOT NULL,
    brokerage REAL,
    tax REAL,
    net_amount REAL NOT NULL,
    trade_id TEXT UNIQUE,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 持仓表 (positions)
```sql
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    quantity INTEGER NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    unrealized_pl REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code)
);
```

#### 3.1.3 行情数据表 (market_data)
```sql
CREATE TABLE IF NOT EXISTS market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    trading_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL NOT NULL,
    volume INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trading_date)
);
```

#### 3.1.4 情绪/日志表 (trading_logs)
```sql
CREATE TABLE IF NOT EXISTS trading_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,
    content TEXT NOT NULL,
    emotion TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.5 对话历史表 (chat_history)
```sql
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_message TEXT NOT NULL,
    assistant_message TEXT NOT NULL,
    conversation_id TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.6 用户配置表 (user_config)
```sql
CREATE TABLE IF NOT EXISTS user_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 数据流程

#### 3.2.1 交易数据导入流程
```
1. 用户上传CSV/Excel格式的交割单
2. 交割单导入器读取文件内容
3. 数据验证器验证数据格式和完整性
4. 数据标准化器清洗和标准化数据
5. 数据被写入trades表
6. 自动更新positions表
7. 生成导入报告并返回给用户
```

#### 3.2.2 情绪/日志处理流程
```
1. 用户输入情绪/日志文本
2. 日志处理器接收文本
3. 文本被送入Cognee进行实体与关系抽取
4. 抽取的实体和关系存储到知识图谱
5. 文本内容存储到trading_logs表
6. 返回处理结果给用户
```

#### 3.2.3 对话交互流程
```
1. 用户输入查询
2. 对话管理模块分析查询类型
3. 如需数据查询，调用Text-to-SQL生成SQL
4. 执行SQL查询获取结果
5. 从Cognee中检索相关图谱上下文
6. 组合Prompt并调用Ollama
7. 存储对话历史
8. 返回回复给用户
```

## 4. 接口定义

### 4.1 前端与应用层接口

#### 4.1.1 数据导入接口
```python
# 导入交割单
POST /api/import/trades
参数：
- file: 上传的CSV/Excel文件
返回：
- status: 导入状态
- message: 导入结果消息
- data: 导入的数据统计信息
```

#### 4.1.2 文档导入接口
```python
# 导入策略文档
POST /api/import/documents
参数：
- file: 上传的PDF/Markdown/TXT文件
- document_type: 文档类型 ('strategy'/'philosophy')
返回：
- status: 导入状态
- message: 导入结果消息
- data: 导入的文档信息
```

#### 4.1.3 情绪/日志输入接口
```python
# 输入情绪/日志
POST /api/logs
参数：
- content: 日志内容
- log_date: 日志日期
返回：
- status: 处理状态
- message: 处理结果消息
- data: 日志ID和处理信息
```

#### 4.1.4 对话接口
```python
# 发送对话消息
POST /api/chat
参数：
- message: 用户消息
- conversation_id: 对话ID（可选）
返回：
- status: 处理状态
- message: 处理结果消息
- data:
  - assistant_message: 助手回复
  - conversation_id: 对话ID
  - context: 使用的上下文信息
```

#### 4.1.5 知识图谱接口
```python
# 获取知识图谱可视化数据
GET /api/graph/visualize
参数：
- filter: 筛选条件（可选）
返回：
- status: 处理状态
- message: 处理结果消息
- data: 图谱可视化数据

# 检索图谱实体和关系
POST /api/graph/retrieve
参数：
- query: 检索查询
- entity_types: 实体类型筛选（可选）
- relationship_types: 关系类型筛选（可选）
返回：
- status: 处理状态
- message: 处理结果消息
- data: 检索到的实体和关系
```

### 4.2 应用层与核心服务层接口

#### 4.2.1 LLM服务接口
```python
# 调用本地LLM
def call_ollama(prompt: str, model: str = "qwen2.5:latest", temperature: float = 0.7) -> str:
    """
    调用本地Ollama服务生成文本
    
    参数：
    - prompt: 输入提示
    - model: 使用的模型名称
    - temperature: 生成温度
    
    返回：
    - 生成的文本
    """
```

#### 4.2.2 Cognee服务接口
```python
# 向Cognee添加文档
def add_to_cognee(content: str, content_type: str = "text/plain") -> str:
    """
    将内容添加到Cognee知识图谱
    
    参数：
    - content: 文档内容
    - content_type: 内容类型
    
    返回：
    - 文档ID
    """

# 从Cognee检索相关信息
def retrieve_from_cognee(query: str, limit: int = 10) -> list:
    """
    从Cognee知识图谱中检索相关信息
    
    参数：
    - query: 检索查询
    - limit: 返回结果数量限制
    
    返回：
    - 检索到的实体和关系列表
    """

# 可视化Cognee知识图谱
def visualize_cognee_graph() -> str:
    """
    生成Cognee知识图谱的可视化HTML
    
    返回：
    - 可视化HTML内容
    """
```

#### 4.2.3 数据处理服务接口
```python
# 清洗和标准化交易数据
def clean_trade_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    清洗和标准化交易数据
    
    参数：
    - data: 原始交易数据
    
    返回：
    - 清洗后的交易数据
    """

# 计算交易指标
def calculate_trade_metrics(data: pd.DataFrame) -> dict:
    """
    计算交易指标
    
    参数：
    - data: 交易数据
    
    返回：
    - 交易指标字典
    """

# 获取行情数据
def get_market_data(stock_codes: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取行情数据
    
    参数：
    - stock_codes: 股票代码列表
    - start_date: 开始日期
    - end_date: 结束日期
    
    返回：
    - 行情数据
    """
```

## 5. 技术栈选择与理由

### 5.1 核心技术栈

| 技术组件 | 选择 | 版本 | 理由 |
|---------|------|------|------|
| 前端框架 | Streamlit | 1.33.0+ | 快速构建数据可视化Web应用，Python原生支持，适合数据科学家和开发者 |
| 本地LLM引擎 | Ollama | 0.1.30+ | 支持本地部署多种LLM模型（Qwen2.5/Llama3.1），无云端依赖，确保隐私 |
| 知识图谱 | Cognee | 最新版 | 专为个人知识管理设计，支持本地部署，适合构建交易知识图谱 |
| 数据库 | SQLite | 3.40.0+ | 轻量级本地数据库，无需服务器，适合个人使用，性能满足需求 |
| 数据处理 | Pandas | 2.2.0+ | Python数据处理库，适合处理交易数据和生成统计报告 |
| 文档处理 | PyPDF2 | 3.0.1+ | Python PDF处理库，用于提取PDF文档内容 |
| 行情数据 | AkShare | 1.10.0+ | 开源财经数据接口库，支持A股数据，本地可部署 |

### 5.2 技术选择理由

1. **本地化与隐私保护**：
   - 所有技术组件均支持本地部署，无云端依赖
   - 数据存储在本地SQLite和Cognee知识图谱中
   - LLM推理在本地Ollama中进行，确保数据不泄露

2. **易用性与快速开发**：
   - Streamlit提供快速构建Web应用的能力
   - Python生态系统成熟，有丰富的金融数据分析库
   - Cognee提供简单的API接口，易于集成知识图谱功能

3. **性能与可扩展性**：
   - SQLite在单用户场景下性能优秀
   - Ollama支持多种LLM模型，可根据硬件性能选择
   - 模块化设计，便于后续功能扩展

4. **成本与维护**：
   - 所有技术均为开源或免费使用
   - 维护成本低，适合个人项目
   - 社区活跃，问题解决速度快

## 6. 潜在技术挑战与解决方案

### 6.1 技术挑战

#### 6.1.1 本地LLM性能问题
- **挑战**：本地LLM模型推理速度可能较慢，影响用户体验
- **解决方案**：
  - 提供模型选择界面，允许用户根据硬件性能选择合适的模型
  - 优化Prompt设计，减少模型推理负担
  - 实现模型缓存机制，复用相似查询的结果

#### 6.1.2 知识图谱构建质量
- **挑战**：从非结构化文本中准确抽取实体和关系难度较大
- **解决方案**：
  - 设计专门的Prompt模板，提高实体和关系抽取准确率
  - 提供人工校正功能，允许用户手动调整图谱内容
  - 逐步优化抽取算法，基于用户反馈改进

#### 6.1.3 数据导入兼容性
- **挑战**：不同券商的交割单格式可能存在差异
- **解决方案**：
  - 支持多种交割单格式识别和转换
  - 提供数据映射界面，允许用户自定义字段映射
  - 实现数据验证功能，检测和提示格式问题

#### 6.1.4 系统性能优化
- **挑战**：随着数据量增长，系统性能可能下降
- **解决方案**：
  - 实现数据索引，提高查询效率
  - 定期清理和优化数据库
  - 提供数据归档功能，管理历史数据

### 6.2 安全与隐私挑战

#### 6.2.1 数据安全
- **挑战**：本地数据需要防止未授权访问
- **解决方案**：
  - 实现用户认证机制
  - 对敏感数据进行加密存储
  - 提供数据备份和恢复功能

#### 6.2.2 隐私保护
- **挑战**：确保所有数据处理都在本地进行
- **解决方案**：
  - 禁用所有外部API调用（除必要的本地服务）
  - 实现网络监控，防止意外数据泄露
  - 提供隐私设置，允许用户控制数据使用范围

## 7. 系统部署架构

### 7.1 本地部署方案

```
┌─────────────────────────────────────────────────────────┐
│                     本地计算机                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │                     Python虚拟环境                   │ │
│ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │
│ │ │  Streamlit  │ │   Ollama    │ │   Cognee        │ │ │
│ │ │  Web应用    │ │  LLM服务    │ │ 知识图谱服务    │ │ │
│ │ └─────────────┘ └─────────────┘ └─────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │                     SQLite                      │ │ │
│ │ │  交易数据库    对话历史数据库    配置数据库       │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 7.2 部署步骤

1. **环境准备**：
   - 安装Python 3.10+ 
   - 安装Ollama并下载所需的LLM模型
   - 创建Python虚拟环境

2. **依赖安装**：
   - 安装项目所需的Python依赖包
   - 配置Cognee和Streamlit

3. **数据库初始化**：
   - 创建SQLite数据库
   - 创建必要的数据表

4. **应用启动**：
   - 启动Streamlit Web应用
   - 验证各服务正常运行

### 7.3 维护与更新

- 定期备份SQLite数据库和Cognee知识图谱
- 及时更新依赖包版本
- 根据用户反馈优化系统功能
- 监控系统性能并进行必要的优化

## 8. 系统扩展性设计

### 8.1 功能扩展性
- 模块化设计，便于添加新功能模块
- 提供插件接口，支持第三方功能扩展
- 设计灵活的数据模型，支持未来数据类型扩展

### 8.2 性能扩展性
- 支持数据库分片（未来多用户场景）
- 支持LLM模型横向扩展（多模型并行推理）
- 设计缓存机制，提高系统响应速度

### 8.3 技术扩展性
- 支持切换不同的本地LLM模型
- 支持接入外部API（如需要）
- 支持不同的前端框架（如Chainlit）

## 9. 总结

本系统设计方案基于需求分析文档，构建了一个完整的本地化个人交易记忆系统。系统采用分层架构，包括前端层、应用层、核心服务层和数据存储层。核心功能包括数据导入与管理、知识图谱构建与检索、交易分析与对话交互。所有技术组件均支持本地部署，确保数据隐私和安全。系统设计考虑了性能优化、可扩展性和用户体验，为后续开发提供了清晰的技术路线图。