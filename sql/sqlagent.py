# import os
import re
import ast
import sqlite3
import pandas as pd
import streamlit as st

# from langchain_community.agent_toolkits import SQLDatabaseToolkit
# from langchain_core.messages import SystemMessage, HumanMessage
# from langgraph.prebuilt import create_react_agent
# from langchain.agents.agent_toolkits import create_retriever_tool
# from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# from langchain_community.embeddings import OllamaEmbeddings
from sql.db_connection import db_connection
from sql.llm import llm
from sql.vector_db_manager import load_vector_db, create_vector_db_from_texts
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
# from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from apis.llm_api import LLMAPI

# 全域變數，用來保存已建立的向量資料庫
vector_db = None


class SQLAgent:
    def __init__(self, chat_session_data):
        self.chat_session_data = chat_session_data

    # 初始化向量資料庫
    def initialize_vector_db(self):
        global vector_db
        if vector_db is None:
            # 如果向量資料庫尚未初始化，從檔案中載入
            vector_db = load_vector_db()
        return vector_db

    # 執行查詢並將結果以列表形式返回
    def query_as_list(self, db, query):
        res = db.run(query)
        # 使用 set 去重後返回列表
        return list(set([el for sub in ast.literal_eval(res) for el in sub if el]))

    # 檢查字串是否包含 GPT-4o 的部署名稱
    def check_gpt_4o(self, string):
        return "deployment_name='gpt-4o'" in string

    # 檢查字串是否包含 GPT-4o-mini 的部署名稱
    def check_gpt_4o_mini(self, string):
        return "deployment_name='gpt-4o-mini'" in string

    # 主函式，處理 SQL 查詢
    def agent(self, query):
        # 連接資料庫
        db_name = self.chat_session_data.get('db_name')
        db_source = self.chat_session_data.get('db_source')
        db = db_connection(db_name, db_source)

        # 初始化 LLM 模型
        SQL_llm, chat = self.initialize_llm()

        # 檢查 LLM 是否為 GPT-4o 或 GPT-4o-mini
        # gpt4o_check, gpt4o_mini_check = 0, 0
        # if self.check_gpt_4o(str(SQL_llm)):
        #     gpt4o_check = 1
        # if self.check_gpt_4o_mini(str(SQL_llm)):
        #     gpt4o_mini_check = 1

        # 根據資料庫名稱獲取提示模板
        prompt_template = self.get_prompt_template(db_name)
        prompt = prompt_template.format(input=query, table_info=db.get_context()["table_info"])

        max_retries, retries = 9, 0
        response = None

        # 嘗試多次執行查詢，直到成功或達到最大重試次數
        while retries <= max_retries:
            try:
                # 執行查詢鏈
                response = self.process_query_chain(prompt, db, gpt4o_check, gpt4o_mini_check)
                if response:
                    break
            except Exception as e:
                error_message = str(e)
                # 如果錯誤訊息不包含 "Invalid" 或 "error"，則拋出異常
                if "Invalid" not in error_message.lower() and "error" not in error_message.lower():
                    raise e

            retries += 1

        # 如果查詢成功，顯示結果
        if response:
            return self.fetch_and_display_results(response, db_name)

        st.write("None")
        return None

    # 初始化 LLM，根據內部 LLM 模式進行配置
    def initialize_llm(self):
        mode = self.chat_session_data.get('mode')
        if mode == '內部LLM':
            # SQL_model: 生成 SQL 語法的 LLM
            SQL_model = "wangshenzhi/llama3.1_8b_chinese_chat"
            SQL_api_base = 'http://10.5.61.81:11433/v1'
            SQL_llm = llm(SQL_model, SQL_api_base)

            # chat_model: 分析 DB 並做出總結的 LLM
            chat_model = "wangshenzhi/llama3.1_8b_chinese_chat"
            chat_api_base = 'http://10.5.61.81:11433/v1'
            chat = llm(chat_model, chat_api_base)

            # 為了 DB 紀錄
            self.chat_session_data['model'] = SQL_model
        else:
            # 外部LLM
            llm_option = self.chat_session_data.get('llm_option')
            SQL_llm = LLMAPI.get_llm(mode, llm_option)
            chat = LLMAPI.get_llm(mode, llm_option)
            st.write(SQL_llm)
        return SQL_llm, chat

    # 根據資料庫名稱取得對應的提示模板
    def get_prompt_template(self, db_name):
        templates = {
            "CC17": """
                You are an SQLite expert... [內容已截斷以便簡潔]
            """,
            "netincome": """
                You are an SQLite expert... [內容已截斷以便簡潔]
            """
        }
        return PromptTemplate.from_template(templates.get(db_name, ""))

    # 執行查詢鏈，並處理 GPT-4o 或 GPT-4o-mini 的查詢格式
    def process_query_chain(self, prompt, db, gpt4o_check, gpt4o_mini_check):
        write_query = create_sql_query_chain(self.SQL_llm, db)
        execute_query = QuerySQLDataBaseTool(db=db)
        validation_chain = self.get_validation_chain(db)

        query_result = write_query.invoke({"question": prompt})
        sql_query = self.extract_sql_query(query_result, gpt4o_check, gpt4o_mini_check)
        validated_query = validation_chain.invoke({"query": sql_query})

        return self.run_query_with_retries(sql_query, validated_query, execute_query)

    # 獲取查詢驗證鏈
    def get_validation_chain(self, db):
        system_msg = """
            Double check the user's {dialect} query for common mistakes... [內容已截斷以便簡潔]
        """
        return ChatPromptTemplate.from_messages(
            [("system", system_msg), ("human", "{query}")]
        ).partial(dialect=db.dialect)

    # 從查詢結果中提取 SQL 查詢語句
    def extract_sql_query(self, result, gpt4o_check, gpt4o_mini_check):
        if gpt4o_check or gpt4o_mini_check:
            pattern = r"(SELECT.*?;)"
            match = re.search(pattern, result, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        return result if result.endswith(';') else result + ';'

    # 執行查詢並重試多次，直到成功或達到最大重試次數
    def run_query_with_retries(self, sql_query, validated_query, execute_query):
        result_sql = execute_query.invoke({"query": sql_query})
        result_validated = execute_query.invoke({"query": validated_query})
        return self.validate_query_results(result_sql, result_validated)

    # 驗證查詢結果是否有效
    def validate_query_results(self, result_sql, result_validated):
        def is_valid(query):
            return query and 'error' not in query.lower() and 'invalid' not in query.lower()

        if is_valid(result_sql):
            return result_sql
        if is_valid(result_validated):
            return result_validated
        return None

    # 提取並顯示查詢結果
    def fetch_and_display_results(self, response, db_name):
        conn = sqlite3.connect(f"{db_name}.db")
        df = pd.read_sql_query(response, conn)

        if df.empty:
            st.write("None")
        elif len(df.to_string()) <= 600:
            st.write(df)
        else:
            st.download_button("下載結果CSV文件", data=df.to_csv(index=False).encode('utf-8-sig'),
                               file_name='query_result.csv', mime='text/csv')

        return response
