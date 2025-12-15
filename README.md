# MyTradeMind - 本地化个人交易记忆系统

## 项目概述

MyTradeMind是一个基于本地存储和AI技术的个人交易记忆系统，旨在帮助交易者记录、分析和反思自己的交易行为，提升交易决策能力。该系统采用隐私优先的设计理念，所有数据都存储在本地，确保用户交易信息的安全性。

## 核心功能

### 1. 数据导入与管理
- 支持CSV/Excel格式的交易数据导入
- 智能列映射和数据清洗功能
- 自动检测交易类型、股票代码、价格等关键信息
- 保留原始数据，支持数据追溯和验证

### 2. 知识图谱分析
- 使用Cognee构建交易知识图谱
- 分析交易行为、情绪和结果的关联关系
- 识别交易模式和决策模式
- 可视化知识图谱结构

### 3. AI聊天助手
- 集成本地LLM（Ollama），支持自然语言交互
- 基于交易数据和知识图谱提供智能分析
- 支持Text-to-SQL查询，快速获取交易统计信息
- 提供交易决策建议和反思引导

### 4. 交易分析与可视化
- 持仓分析和组合管理
- 交易绩效评估和风险分析
- 图表化展示交易历史和趋势
- 多维度统计分析

## 技术栈

- **前端框架**：Streamlit
- **数据库**：SQLite
- **知识图谱**：Cognee
- **本地LLM**：Ollama (Qwen2.5/Llama3.1)
- **数据处理**：Pandas
- **可视化**：Plotly
- **其他**：SQLAlchemy, Regex

## 安装与配置

### 1. 环境要求
- Python 3.10+
- Ollama
- 支持的操作系统：Windows, macOS, Linux

### 2. 安装步骤

#### 2.1 克隆项目
```bash
git clone <项目地址>
cd PersonalTrader
```

#### 2.2 创建虚拟环境
```bash
python -m venv mytrademind-env
# 激活虚拟环境
# Windows
mytrademind-env\Scripts\activate
# macOS/Linux
source mytrademind-env/bin/activate
```

#### 2.3 安装依赖
```bash
pip install -r requirements.txt
```

#### 2.4 配置Ollama
1. 安装Ollama：https://ollama.com/download
2. 拉取推荐模型：
   ```bash
   ollama pull qwen2.5:7b-instruct
   ollama pull llama3.1:8b-instruct
   ```

## 使用方法

### 1. 启动应用
```bash
streamlit run app.py
```

### 2. 数据导入
1. 准备交易数据文件（CSV/Excel格式）
2. 在"数据导入"页面上传文件
3. 系统自动检测列映射关系
4. 点击"导入"按钮完成数据导入

### 3. 知识图谱构建
1. 在"知识图谱"页面点击"构建图谱"
2. 系统将基于导入的交易数据构建知识图谱
3. 可以查看和探索构建好的知识图谱

### 4. 智能聊天
1. 在"聊天助手"页面输入问题
2. 系统将基于交易数据和知识图谱提供回答
3. 支持的问题类型：
   - 交易统计查询："我最近一个月的交易次数是多少？"
   - 持仓分析："我目前持有的股票有哪些？"
   - 交易反思："我的交易模式有什么问题？"
   - 决策建议："针对这只股票，我应该如何操作？"

### 5. 交易分析
1. 在"交易分析"页面查看各种分析图表
2. 可以选择不同的时间范围和分析维度
3. 查看持仓明细、交易绩效、风险指标等

## 项目结构

```
PersonalTrader/
├── src/
│   ├── utils/
│   │   └── database.py         # 数据库管理模块
│   ├── data_ingestion/
│   │   └── data_importer.py    # 数据导入模块
│   ├── knowledge_graph/
│   │   └── graph_manager.py    # 知识图谱管理
│   ├── llm/
│   │   └── llm_manager.py      # LLM集成模块
│   ├── analysis/
│   │   └── trade_analyzer.py   # 交易分析模块
│   └── visualization/
│       └── visualizer.py       # 可视化模块
├── data/
│   └── trading.db              # SQLite数据库文件
├── config/
│   └── config.py               # 配置文件
├── tests/
│   ├── utils/
│   ├── data_ingestion/
│   ├── knowledge_graph/
│   └── llm/
├── app.py                      # 主应用入口
├── requirements.txt            # 依赖包列表
└── README.md                   # 项目说明文档
```

## 数据安全与隐私

MyTradeMind采用本地优先的设计理念，所有数据都存储在用户本地设备上，不会上传到任何服务器。具体措施包括：

- 交易数据存储在本地SQLite数据库中
- 知识图谱构建在本地完成
- LLM模型运行在本地（Ollama）
- 不收集用户的任何个人信息
- 支持数据导出和备份功能

## 开发与贡献

### 开发环境设置

1. 安装开发依赖：
```bash
pip install -e .
pip install pytest
```

2. 运行测试：
```bash
python -m unittest discover tests
```

### 代码规范

- 遵循PEP 8代码规范
- 使用Type Hints
- 编写单元测试
- 保持代码简洁和可维护性

## 版本计划

### MVP版本 (v0.1)
- 基础数据导入功能
- 简单的交易记录展示
- 基本的聊天功能
- 知识图谱初步构建

### v0.2 版本
- 完善的交易分析功能
- 更智能的知识图谱分析
- 支持更多数据格式
- 改进的UI界面

### v0.3 版本
- 情绪分析和交易心理模型
- 多用户支持
- 数据导出和分享功能
- 更高级的可视化图表

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：

- Email: [your-email@example.com]
- GitHub Issues: [项目GitHub地址]

---

**免责声明**：本项目仅用于个人交易记录和分析，不构成任何投资建议。投资有风险，决策需谨慎。
