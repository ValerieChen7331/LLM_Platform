from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
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
import streamlit as st
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import sqlite3
import pandas as pd
from apis.llm_api import LLMAPI

# 全域變數，用來保存已建立的向量資料庫
vector_db = None


def initialize_vector_db(db):
    global vector_db
    if vector_db is None:
        # 嘗試從檔案中載入向量資料庫
        vector_db = load_vector_db()
    return vector_db


def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    return list(set(res))


from langchain_openai import ChatOpenAI


# from langchain.llms import Ollama
# from langchain_community.chat_models import ChatOllama

def llm2(model):
    # llm = ChatOllama(base_url=openai_api_base, model=model)
    llm = ChatOpenAI(api_key="ollama", model=model)
    return llm


def agent(query, db_name, db_source):
    # MSSQL DB
    db = db_connection(db_name, db_source)

    if st.session_state.get('mode') == '內部LLM':
        # SQL_LLM
        # SQL_LLM
        # openai_api_base = 'http://10.5.61.81:11433/v1'
        # openai_api_base = 'http://127.0.0.1:11435'
        openai_api_base = 'http://10.5.61.81:11433/v1'
        # model ="sqlcoder"
        # model ="deepseek-coder-v2"
        #model = "codeqwen"
        # model ="codeqwen"
        model = "wangshenzhi/llama3.1_8b_chinese_chat"
        SQL_llm = llm(model, openai_api_base)

        # 為了DB紀錄
        st.session_state['model'] = model

        # CHAT_LLM(With tool training)
        openai_api_base = 'http://10.5.61.81:11433/v1'
        model = "wangshenzhi/llama3.1_8b_chinese_chat"
        chat = llm(model, openai_api_base)
        # chat = llm2(chat_model)

    else:
        SQL_llm = LLMAPI.get_llm()
        chat = LLMAPI.get_llm()

    max_retries=9
    #chat = llm2(chat_model)
    # 初始化或使用已存在的向量資料庫
    llm_context_prompt_template = """
    You are an SQLite expert. 
    Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the FETCH FIRST n ROWS ONLY clause as per SQLite. 
    You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use TRUNC(SYSDATE) function to get the current date, if the question involves "today".
    Use the following format:
    Question: Question here
    SQLQuery: SQL Query to run
    SQLResult: Result of the SQLQuery
    Answer: Final answer here
    Only use the following tables:
    {table_info} 
    Below are a number of examples of questions and their corresponding SQL queries:

    User input: table CC17叫做大額費用明細表。其中，若詢問110年02月，代表要找YM='11002'、DP代表部門、ACCT表示會計科目、'6321AA'表示用人費用、AMT表示金額。在前述規則下，請告訴我111年01月，7300部門的用人費用金額合計是多少?
    SQL query: SELECT SUM(AMT) FROM CC17 WHERE YM = '11101' AND DP = '7300' AND ACCT = '6321AA';
        

    Question: {input}   
    """

    LLM_CONTEXT_PROMPT = PromptTemplate.from_template(llm_context_prompt_template)
    db = db_connection(db_name, db_source)
    
    # Get database context (table information)
    context = db.get_context()
    table_info = context["table_info"]

    # Create the query chain
    write_query = create_sql_query_chain(SQL_llm, db)
    execute_query = QuerySQLDataBaseTool(db=db)
    chain = write_query | execute_query


    # 定義第二個模型的 Prompt，用於驗證 SQL 查詢
    system = """Double check the user's {dialect} query for common mistakes, including:
    - Using NOT IN with NULL values
    - Using UNION when UNION ALL should have been used
    - Using BETWEEN for exclusive ranges
    - Data type mismatch in predicates
    - Properly quoting identifiers
    - Using the correct number of arguments for functions
    - Casting to the correct data type
    - Using the proper columns for joins
    
    If there are any of the above mistakes, rewrite the query.
    If there are no mistakes, just reproduce the original query with no further commentary.
    
    Output the final SQL query only."""
    
    # 驗證 Prompt Template
    prompt2 = ChatPromptTemplate.from_messages(
        [("system", system), ("human", "{query}")]
    ).partial(dialect=db.dialect)


    validation_chain = prompt2 | SQL_llm | StrOutputParser()



    # Generate the initial prompt
    prompt = LLM_CONTEXT_PROMPT.format(input=query, table_info=table_info, top_k=20)
    
    retries = 0
    response = None
    def fetch_query_result_with_headers(query, db_path):
        conn = sqlite3.connect("CC17.db")
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        df = pd.DataFrame(result, columns=headers)
        return df
    while retries <= max_retries:
        try:
            
            query_result = write_query.invoke({"question": prompt})
            sql_query = query_result  # 取得 SQL 查詢
            st.write("sql_query",sql_query)
            validated_query = validation_chain.invoke({"query": sql_query})
            st.write("validated_query ",validated_query)
            execute_result = execute_query.invoke({"query": validated_query})
            # Invoke the chain with the generated prompt
            #response = chain.invoke({"question": prompt})
            response=execute_result 
            response3=str(response)
            st.write("execute_result",execute_result)
            # Check if response contains invalid column name error
            if re.search(r"error", response3, re.IGNORECASE) or re.search(r"Invalid", response3, re.IGNORECASE) or re.search(r"Error", response3, re.IGNORECASE) :
                retries += 1 
                print(f"Retrying... ({retries}/{max_retries})")
                continue  # Continue retrying if invalid column name error is found

            break  # Break if the response is successful

        except Exception as e:
            error_message = str(e)
            print(f"Error occurred: {error_message}")
            
            # Check for invalid column name error
            if "Invalid" or "error" in error_message:
                print("Invalid column name error detected, retrying...")
            else:
                # Raise other exceptions directly
                raise e
        if retries>=max_retries:
            break    
        retries += 1
    columns=fetch_query_result_with_headers(sql_query ,db)
    st.write("fetch_query_result_with_headers",columns)

    # query2=str(query)
        # sql_query2=str(sql_query)
        # response2=str(response)
        # st.write(query2)
        # st.write(sql_query2)
        # st.write(response2)
        # # 將問題、查詢和結果傳遞給 LLM
        # final_prompt = f"""
        # Given the following user Question, corresponding SQL query, and SQL result, answer the user Question.
        # YOU MUST reply in Chinese.
        # Please reference the following columns: YM、CO、DIV、PLD、DP、ACCT、EGNO、EGNM、URID、MTNO、MTNM、SUMR、QTY、AMT、PURURCOMT、VOCHCSUMER、FBEN、USSHNO、VOCHNO、IADAT、PVNO、SALID、JBDP、IT.
        # Question: {query2}
        # SQL Query: {sql_query2}
        # SQL Result: {response2}
        # Output Format: Return the answer in DataFrame format with the appropriate column names.
        # """
        # final_answer = chat.invoke(final_prompt)
        # final_answer=str(final_answer)
    return response