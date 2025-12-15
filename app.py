import streamlit as st
import os
import uuid
from datetime import datetime
from src.utils.database import DatabaseManager
from src.data_ingestion.data_importer import DataImporter
from src.llm.llm_manager import LLMManager
from src.knowledge_graph.graph_manager import GraphManager
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(
    page_title="MyTradeMind - 个人交易记忆系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化管理器
@st.cache_resource
def get_managers():
    db_manager = DatabaseManager()
    data_importer = DataImporter()
    llm_manager = LLMManager()
    graph_manager = GraphManager()
    
    # 初始化数据库
    db_manager.init_database()
    
    # 初始化知识图谱
    graph_manager.initialize()
    
    return db_manager, data_importer, llm_manager, graph_manager

db_manager, data_importer, llm_manager, graph_manager = get_managers()

# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "聊天界面"

# 侧边栏
with st.sidebar:
    st.title("📊 MyTradeMind")
    st.write("个人交易记忆系统")
    
    # 选项卡选择
    tab = st.radio(
        "选择功能",
        ["聊天界面", "数据导入", "交易分析", "知识图谱"],
        index=["聊天界面", "数据导入", "交易分析", "知识图谱"].index(st.session_state.selected_tab)
    )
    
    st.session_state.selected_tab = tab
    
    st.divider()
    
    # 关于信息
    st.write("### 关于")
    st.write("一个本地化的个人交易分析系统，使用知识图谱和本地LLM进行交易数据分析和可视化。")
    st.write("数据存储在本地，保护您的隐私。")

# 聊天界面
if st.session_state.selected_tab == "聊天界面":
    st.title("💬 交易助手")
    st.write("与您的交易数据进行对话，获取分析和洞察。")
    
    # 聊天历史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 用户输入
    user_input = st.chat_input("请输入您的问题或请求...")
    
    if user_input:
        # 显示用户消息
        with st.chat_message("user"):
            st.write(user_input)
        
        # 添加到聊天历史
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 生成响应
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                # 获取增强响应
                response = llm_manager.get_enhanced_response(
                    user_input, 
                    st.session_state.chat_history[:-1]  # 不包括当前用户输入
                )
                
                st.write(response)
        
        # 添加到聊天历史和数据库
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # 保存到数据库
        db_manager.add_chat_message(
            session_id=st.session_state.session_id,
            role="user",
            content=user_input
        )
        
        db_manager.add_chat_message(
            session_id=st.session_state.session_id,
            role="assistant",
            content=response
        )
    
    # 清除聊天历史
    if st.button("清除聊天历史", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()

# 数据导入界面
elif st.session_state.selected_tab == "数据导入":
    st.title("📥 数据导入")
    st.write("导入您的交易数据，支持CSV和Excel格式。")
    
    # 文件上传
    uploaded_file = st.file_uploader(
        "选择交易数据文件",
        type=["csv", "xlsx", "xls"],
        help="支持CSV和Excel格式的交易数据文件"
    )
    
    if uploaded_file:
        try:
            # 读取文件
            df = data_importer.read_file(uploaded_file)
            
            # 显示文件内容预览
            st.write("### 文件内容预览")
            st.dataframe(df.head(10))
            
            # 自动检测列映射
            column_mapping = data_importer.detect_columns(df)
            
            # 显示列映射结果
            st.write("### 列映射检测结果")
            col_mapping_expander = st.expander("查看/调整列映射")
            
            with col_mapping_expander:
                for field, mapped_col in column_mapping.items():
                    column_mapping[field] = st.selectbox(
                        f"{field}",
                        ["无"] + list(df.columns),
                        index=0 if mapped_col is None else list(df.columns).index(mapped_col) + 1,
                        key=f"col_{field}"
                    )
                    
                    # 转换为None如果选择"无"
                    if column_mapping[field] == "无":
                        column_mapping[field] = None
            
            # 导入按钮
            if st.button("导入数据", type="primary"):
                with st.spinner("正在导入数据..."):
                    try:
                        # 保存上传的文件
                        temp_file_path = f"temp_{uuid.uuid4()}{os.path.splitext(uploaded_file.name)[1]}"
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 导入数据
                        imported_count = data_importer.import_data(temp_file_path, column_mapping)
                        
                        # 删除临时文件
                        os.remove(temp_file_path)
                        
                        # 更新知识图谱
                        graph_manager.build_graph_from_trades()
                        
                        st.success(f"成功导入 {imported_count} 条交易记录！")
                        
                    except Exception as e:
                        st.error(f"导入失败: {str(e)}")
                        os.remove(temp_file_path)
                        
        except Exception as e:
            st.error(f"读取文件失败: {str(e)}")
    
    # 显示当前数据库状态
    st.divider()
    st.write("### 当前数据库状态")
    
    # 显示交易记录统计
    trades = db_manager.get_all_trades(limit=10000)
    positions = db_manager.get_current_positions()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("总交易记录数", len(trades))
    with col2:
        st.metric("当前持仓股票数", len(positions))
    
    # 显示最近交易记录
    st.write("### 最近10条交易记录")
    if trades:
        recent_trades = trades[:10]
        df_trades = pd.DataFrame(recent_trades)
        st.dataframe(df_trades)
    else:
        st.write("暂无交易记录")

# 交易分析界面
elif st.session_state.selected_tab == "交易分析":
    st.title("📈 交易分析")
    st.write("分析您的交易数据，获取可视化洞察。")
    
    # 获取交易数据
    trades = db_manager.get_all_trades(limit=10000)
    
    if not trades:
        st.warning("暂无交易数据，无法进行分析")
    else:
        # 转换为DataFrame
        df_trades = pd.DataFrame(trades)
        
        # 数据预处理
        df_trades['trade_date'] = pd.to_datetime(df_trades['trade_date'])
        df_trades['amount'] = df_trades['amount'].astype(float)
        df_trades['net_amount'] = df_trades['net_amount'].astype(float)
        
        # 创建分析选项卡
        tab1, tab2, tab3, tab4 = st.tabs(["交易概览", "持仓分析", "时间分析", "交易类型分析"])
        
        with tab1:
            st.write("### 交易概览")
            
            # 总交易金额
            total_buy = df_trades[df_trades['trade_type'] == 'BUY']['amount'].sum()
            total_sell = df_trades[df_trades['trade_type'] == 'SELL']['amount'].sum()
            total_commission = df_trades['brokerage'].sum()
            total_tax = df_trades['tax'].sum()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总买入金额", f"¥{total_buy:,.2f}")
            with col2:
                st.metric("总卖出金额", f"¥{total_sell:,.2f}")
            with col3:
                st.metric("总佣金", f"¥{total_commission:,.2f}")
            with col4:
                st.metric("总税费", f"¥{total_tax:,.2f}")
            
            # 股票交易次数排名
            st.write("### 股票交易次数排名")
            trade_counts = df_trades['stock_code'].value_counts().head(10)
            fig = px.bar(trade_counts, x=trade_counts.index, y=trade_counts.values, 
                        labels={'x': '股票代码', 'y': '交易次数'}, title="股票交易次数")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.write("### 持仓分析")
            
            positions = db_manager.get_current_positions()
            
            if not positions:
                st.write("当前无持仓")
            else:
                df_positions = pd.DataFrame(positions)
                
                # 持仓数量分布
                fig = px.pie(df_positions, names='stock_code', values='quantity', 
                            title="持仓数量分布")
                st.plotly_chart(fig, use_container_width=True)
                
                # 持仓成本分布
                fig = px.pie(df_positions, names='stock_code', values='avg_cost', 
                            title="持仓成本分布")
                st.plotly_chart(fig, use_container_width=True)
                
                # 持仓列表
                st.write("### 持仓详情")
                st.dataframe(df_positions)
        
        with tab3:
            st.write("### 时间分析")
            
            # 按月份统计交易金额
            df_trades['month'] = df_trades['trade_date'].dt.strftime('%Y-%m')
            monthly_trades = df_trades.groupby(['month', 'trade_type'])['amount'].sum().reset_index()
            
            fig = px.bar(monthly_trades, x='month', y='amount', color='trade_type', 
                        labels={'amount': '交易金额', 'month': '月份'}, title="月度交易金额")
            st.plotly_chart(fig, use_container_width=True)
            
            # 交易日期分布
            fig = px.histogram(df_trades, x='trade_date', nbins=50, 
                            labels={'trade_date': '交易日期', 'count': '交易次数'}, title="交易日期分布")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab4:
            st.write("### 交易类型分析")
            
            # 买卖比例
            trade_type_counts = df_trades['trade_type'].value_counts()
            fig = px.pie(trade_type_counts, names=trade_type_counts.index, values=trade_type_counts.values, 
                        title="买卖交易比例")
            st.plotly_chart(fig, use_container_width=True)
            
            # 平均交易金额
            avg_trade_amount = df_trades.groupby('trade_type')['amount'].mean()
            fig = px.bar(avg_trade_amount, x=avg_trade_amount.index, y=avg_trade_amount.values, 
                        labels={'x': '交易类型', 'y': '平均交易金额'}, title="平均交易金额")
            st.plotly_chart(fig, use_container_width=True)

# 知识图谱界面
elif st.session_state.selected_tab == "知识图谱":
    st.title("🧠 知识图谱")
    st.write("使用知识图谱可视化您的交易数据和关系。")
    
    # 构建知识图谱
    if st.button("构建/更新知识图谱", type="primary"):
        with st.spinner("正在构建知识图谱..."):
            try:
                count = graph_manager.build_graph_from_trades()
                st.success(f"成功构建知识图谱，处理了 {count} 条交易记录！")
            except Exception as e:
                st.error(f"构建知识图谱失败: {str(e)}")
    
    # 获取图数据
    if st.button("查看知识图谱", type="secondary"):
        with st.spinner("正在获取知识图谱数据..."):
            try:
                graph_data = graph_manager.get_graph_data()
                
                if graph_data:
                    st.write("### 知识图谱节点和关系")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("#### 节点")
                        nodes = graph_data.get('nodes', [])
                        st.write(f"总节点数: {len(nodes)}")
                        if nodes:
                            df_nodes = pd.DataFrame(nodes)
                            st.dataframe(df_nodes.head(20))
                    
                    with col2:
                        st.write("#### 关系")
                        edges = graph_data.get('edges', [])
                        st.write(f"总关系数: {len(edges)}")
                        if edges:
                            df_edges = pd.DataFrame(edges)
                            st.dataframe(df_edges.head(20))
                else:
                    st.warning("知识图谱为空，请先构建知识图谱")
            except Exception as e:
                st.error(f"获取知识图谱数据失败: {str(e)}")
    
    # 知识图谱查询
    st.divider()
    st.write("### 知识图谱查询")
    
    query = st.text_input("输入知识图谱查询", placeholder="例如: 查询与特定股票相关的所有交易")
    
    if st.button("执行查询"):
        with st.spinner("正在查询知识图谱..."):
            try:
                results = graph_manager.query_graph(query)
                if results:
                    st.write("查询结果:")
                    st.json(results, expanded=False)
                else:
                    st.write("未找到相关结果")
            except Exception as e:
                st.error(f"查询知识图谱失败: {str(e)}")

# 页脚
st.divider()
st.write("© 2025 MyTradeMind - 个人交易记忆系统 | 数据本地存储，保护隐私")
