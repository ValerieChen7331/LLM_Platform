from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.exc import OperationalError

from sql.db_connection import db_connection  # 資料庫連線模組
from sql.llm import llm  # LLM 模型

import streamlit as st
from apis.llm_api import LLMAPI  # LLM API 模組
import sqlite3
import pandas as pd
import re

# 根據 session 狀態選擇 LLM 模型
if st.session_state.get('mode') == '內部LLM':  # 如果是內部 LLM 模式
    # SQL_LLM 設定
    openai_api_base = 'http://10.5.61.81:11433/v1'
    model = "codeqwen"  # 選擇 LLM 模型，可選擇其他 model, 如 sqlcoder:15b, deepseek-coder-v2, codeqwen, duckdb-nsql
    SQL_llm = llm(model, openai_api_base)

    # 紀錄使用的 model 以便後續資料庫記錄
    st.session_state['model'] = model

    # CHAT_LLM 設定 (支援工具訓練)
    openai_api_base = 'http://10.5.61.81:11433/v1'
    model = "wangshenzhi/llama3.1_8b_chinese_chat"
    chat = llm(model, openai_api_base)

else:
    # 使用外部的 LLMAPI
    SQL_llm = LLMAPI.get_llm()
    chat = LLMAPI.get_llm()


# 定義執行 SQL 查詢的代理函數
def agent(question, db_name, db_source):
    # 連接 MSSQL 資料庫
    db = db_connection(db_name, db_source)
    print('db:', db)

    # 取得資料庫 schema 資訊
    def get_db_schema(_):
        info = db.get_table_info()
        return info

    # 定義函數以執行 SQL 查詢並打印查詢語句
    def run_query_with_logging(query):
        print("Generated SQL Query:", query)  # 打印出生成的 SQL 查詢
        try:
            # 使用 _execute() 方法，並確保返回 list 結果
            result = db._execute(command=query, fetch="all")  # 確保 _execute() 返回所有資料
            return result
        except (OperationalError, Exception) as e:
            return str(e)

    # 生成 SQL 查詢提示
    gen_sql_prompt = ChatPromptTemplate.from_messages([
        ('system',
         '一開始你應該總是先查看資料庫中的表格 schema：{db_schema}，以了解可以查詢的內容。table CC17叫做大額費用明細表、DP代表部門、ACCT表示會計科目、6322EC表示修護費用。'),
        ('user', '請根據 {db_schema} 生成針對以下問題的 SQL 查詢: "{input}"。\
        查詢應注意以下幾點以避免常見錯誤：\
        1. 在文字欄位查詢時，使用 `COLLATE NOCASE` 來忽略大小寫差異。\
        2. 對所有可能包含空格的文字欄位使用 `TRIM()` 函數來移除前後空白字符。\
        3. 使用 `LIKE` 和萬用字元 `%` 來處理潛在的隱藏字符或空白。\
        4. 使用 `TIMESTAMP` 來處理日期時間欄位，而非 `time` 或 `date`。\
        4. SQL指令務必以SELECT開頭，;結束。\
        查詢「只能」有SQL指令!不可包含任何額外說明!例如：\
        ```sql\
         SELECT * FROM CC17\
        WHERE TRIM(VOCHCSUMR) COLLATE NOCASE LIKE "%PA廠推高機輪胎龜裂更換(實心)%";\
        ```\
        <sql_query>\
        '),
    ])

    # 定義自動擷取 SQL 查詢的函數
    def extract_sql_query(generated_sql_result):
        # 使用正則表達式來匹配 SQL 查詢
        sql_pattern = r"(SELECT.*?;)"
        match = re.search(sql_pattern, generated_sql_result, re.DOTALL)

        if match:
            # 匹配的 SQL 查詢
            extracted_sql = match.group(1)
            return extracted_sql
        else:
            return None

    # 生成 SQL 查詢鏈
    gen_query_chain = (
            RunnablePassthrough.assign(db_schema=get_db_schema)  # 設定資料庫 schema
            | gen_sql_prompt  # 生成 SQL 查詢提示
            | SQL_llm  # 使用 LLM 模型生成 SQL 查詢
            | StrOutputParser()  # 解析生成的結果
    )

    # 執行 SQL 查詢生成鏈並打印查詢
    generated_sql_result = gen_query_chain.invoke({'input': question})
    print(f"Generated SQL Query: {generated_sql_result}")

    # 呼叫函數並擷取 SQL 查詢
    extracted_sql = extract_sql_query(generated_sql_result)
    if extracted_sql:
        print(f"Extracted SQL Query:\n{extracted_sql}")
    else:
        print("No SQL query found.")

    # 執行查詢並取得結果
    result = run_query_with_logging(extracted_sql)
    print('result:', result)  # 打印查詢結果
    print('result type:', type(result))  # 確認結果類型

    # 定義自動提取表頭的函數
    def extract_headers_from_sql(sql_query):
        # 使用正則表達式匹配 SELECT 和 FROM 之間的內容
        pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(pattern, sql_query, re.IGNORECASE)

        if match:
            # 提取欄位部分，並根據逗號分隔
            headers_str = match.group(1)
            headers = [header.strip() for header in headers_str.split(',')]
            return headers
        else:
            return None

    if isinstance(result, list):
        # 如果查詢中包含 '*' 則使用預設的欄位
        if '*' in extracted_sql:
            headers = ['YM', 'CO', 'DIV', 'PLD', 'DP', 'ACCT', 'EGNO', 'EGNM', 'URID', 'MTNO',
                       'MTNM', 'SUMR', 'QTY', 'AMT', 'PURURCOMT', 'VOCHCSUMR',
                       'FBEN', 'USSHNO', 'VOCHNO', 'IADAT', 'PVNO', 'SALID', 'JBDP', 'IT']
        else:
            # 否則提取查詢中的欄位
            headers = extract_headers_from_sql(extracted_sql)

        # 使用 pandas 轉換查詢結果為 DataFrame
        df = pd.DataFrame(result, columns=headers)
        print(headers)
    else:
        df = pd.DataFrame()  # 如果沒有結果，則返回空表格

    print(df)  # 顯示查詢結果表格
    df.to_csv('data.csv',index=False, encoding='utf-8-sig')

    # 生成回答提示
    gen_answer_prompt = ChatPromptTemplate.from_template("""
    根據提供的問題、SQL 查詢及查詢結果，撰寫包含欄位名稱的自然語言回應。
    請勿包含任何額外說明。

    問題: {input}
    SQL 查詢: {query}
    查詢結果: {result}

    回應應按照以下格式撰寫：
    '''
    執行查詢: {query}
    回答: <answer>
    '''
    """)

    # 查詢處理鏈，處理生成的 SQL 查詢並產生最終回答
    query_execution_chain = (
            gen_answer_prompt  # 生成回答提示
            | chat  # 使用 LLM 生成最終回答
    )

    # 傳遞生成的查詢結果給下一個步驟
    response = query_execution_chain.invoke({'result': df, 'query': generated_sql_result, 'input': question})

    return response  # 返回最終回答
