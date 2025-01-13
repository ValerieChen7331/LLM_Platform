from flask import Flask, request, jsonify
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from sql.db_connection import db_connection
from sql.llm import llm
import ast
import re
import os
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from sql.vector_db_manager import load_vector_db, create_vector_db_from_texts
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import sqlite3
import pandas as pd
from apis.llm_api import LLMAPI

app = Flask(__name__)

# 全域變數，用來保存已建立的向量資料庫
vector_db = None

@app.route('/initialize_vector_db', methods=['POST'])
def initialize_vector_db():
    """初始化向量資料庫"""
    global vector_db
    if vector_db is None:
        vector_db = load_vector_db()
    return jsonify({'status': 'success', 'message': 'Vector database initialized'})

@app.route('/query_as_list', methods=['POST'])
def query_as_list():
    """查詢資料庫並將結果作為列表返回"""
    data = request.json
    db = db_connection(data['db_name'], data['db_source'])
    query = data['query']
    try:
        res = db.run(query)
        res = [el for sub in ast.literal_eval(res) for el in sub if el]
        return jsonify({'status': 'success', 'result': list(set(res))})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/agent', methods=['POST'])
def agent():
    """處理代理查詢"""
    data = request.json
    query = data['query']
    db_name = data['db_name']
    db_source = data['db_source']
    # 在這裡放置您的原始代理邏輯
    try:
        # 取得 SQL_LLM 和 Chat LLM
        db = db_connection(db_name, db_source)
        gpt4o_check = 0
        gpt4o_mini_check = 0
        SQL_llm = LLMAPI.get_llm()
        chat = LLMAPI.get_llm()

        # 根據選擇的資料庫建立 Prompt
        if db_name == "CC17":
            llm_context_prompt_template = """
            # SQLite 資料庫專家...
            """
        elif db_name == "netincome":
            llm_context_prompt_template = """
            # SQLite 資料庫專家...
            """
        LLM_CONTEXT_PROMPT = PromptTemplate.from_template(llm_context_prompt_template)
        context = db.get_context()
        table_info = context["table_info"]
        prompt = LLM_CONTEXT_PROMPT.format(input=query, table_info=table_info)

        # 創建 SQL 查詢鏈
        write_query = create_sql_query_chain(SQL_llm, db)
        execute_query = QuerySQLDataBaseTool(db=db)
        chain = write_query | execute_query

        # 執行查詢和驗證
        sql_query = write_query.invoke({"question": prompt})
        if not sql_query.endswith(';'):
            sql_query += ';'
        validated_query = validation_chain.invoke({"query": sql_query})
        validated_query += ';' if not validated_query.endswith(';') else ''

        execute_result_sql_query = execute_query.invoke({"query": sql_query})
        execute_result_validated_query = execute_query.invoke({"query": validated_query})

        # 返回最終結果
        response, _ = return_valid_query(
            execute_result_sql_query, execute_result_validated_query, 0
        )
        return jsonify({'status': 'success', 'response': response})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/fetch_query_result', methods=['POST'])
def fetch_query_result():
    """從資料庫獲取查詢結果，並返回 DataFrame"""
    data = request.json
    query = data['query']
    db_name = data['db_name']
    try:
        df = fetch_query_result_with_headers(query, db_name + ".db")
        return jsonify({'status': 'success', 'data': df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def fetch_query_result_with_headers(query, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    df = pd.DataFrame(result, columns=headers)
    conn.close()
    return df

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
