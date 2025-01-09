from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from sql.db_connection import db_connection
from sql.llm import llm
import ast
import streamlit as st
from langchain.agents.agent_toolkits import create_retriever_tool
from apis.llm_api import LLMAPI

# 向量資料庫的相關函式
from sql.vector_db_manager import load_vector_db

# 全域變數，用來保存已建立的向量資料庫
vector_db = None


# 初始化向量資料庫
def initialize_vector_db(db):
    global vector_db
    if vector_db is None:
        # 嘗試從檔案中載入向量資料庫
        vector_db = load_vector_db()
    return vector_db


# 查詢資料庫並將結果轉換為列表格式
def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    return list(set(res))


# OpenAI 的 LLM 設定
from langchain_openai import ChatOpenAI


# 定義 LLM 模型
def llm2(model):
    # 設定 LLM 為 ChatOpenAI
    llm = ChatOpenAI(api_key="ollama", model=model)
    return llm


# 執行查詢的主要 Agent 函式
def agent(query, db_name, db_source):
    # MSSQL DB 連接
    db = db_connection(db_name, db_source)

    # 判斷是否使用內部 LLM 模式
    if st.session_state.get('mode') == '內部LLM':
        # 使用內部 LLM 模型
        openai_api_base = 'http://10.5.61.81:11433/v1'
        model = "codeqwen"
        SQL_llm = llm(model, openai_api_base)

        # 保存模型名稱以便 DB 紀錄
        st.session_state['model'] = model

        # 設定對話 LLM
        model = "wangshenzhi/llama3.1_8b_chinese_chat"
        chat = llm(model, openai_api_base)
    else:
        # 使用 LLM API
        SQL_llm = LLMAPI.get_llm()
        chat = LLMAPI.get_llm()

    # 初始化或使用已存在的向量資料庫
    vector_db = initialize_vector_db(db)
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    # 檢索工具設定
    description = """用來查找篩選條件。輸入為專有名詞的近似拼寫，輸出為有效的專有名詞。請使用最接近搜尋的專有名詞。"""
    retriever_tool = create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )

    # 建立系統訊息
    system = """你是一個專門用來操作 SQL 資料庫的 Agent。
    根據使用者的問題，創建正確的 SQLite 查詢語句，並查詢結果，返回最相關的答案。
    除非使用者指定了想要查詢的數量，否則每次最多返回 5 個結果。
    你可以根據相關欄位來排序結果，並且不應該查詢所有欄位，只查詢與問題相關的欄位。
    在進行查詢之前，必須仔細檢查查詢語句。如有錯誤，請重新撰寫查詢語句。

    不得對資料庫進行 DML 操作（INSERT、UPDATE、DELETE、DROP 等）。

    你可以訪問以下資料表：{table_names}

    如果需要篩選專有名詞，務必使用 "search_proper_nouns" 工具查找相似的值。"""

    # 插入資料庫的可用表名稱
    system = system.format(table_names=db.get_usable_table_names())
    print('1. system: ', system)
    system_message = SystemMessage(content=system)
    print('2. system_message: ', system_message)

    # 初始化工具包
    toolkit = SQLDatabaseToolkit(db=db, llm=SQL_llm)
    print('3. toolkit: ', toolkit)
    tools = toolkit.get_tools()
    print('4. tools: ', tools)
    tools.append(retriever_tool)

    # 建立 Agent
    agent_executor = create_react_agent(chat, tools, state_modifier=system_message)
    print('5. agent_executor: ', agent_executor)

    # 執行查詢並取得結果
    contents = list(agent_executor.stream({"messages": [HumanMessage(content=query)]}))
    print('6. contents: ', contents)

    # 回傳結果
    st.write(list(agent_executor.stream({"messages": [HumanMessage(content=query)]})))
    return contents[-1]['agent']['messages'][0].content
