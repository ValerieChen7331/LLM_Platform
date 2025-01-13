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

def check_gpt_4o(string):
    return "deployment_name='gpt-4o'" in string
def check_gpt_4o_mini(string):
    return "deployment_name='gpt-4o-mini'" in string


def agent(query, db_name, db_source):
    # MSSQL DB
    db = db_connection(db_name, db_source)
    gpt4o_check=0
    gpt4o_mini_check=0
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
        st.write(SQL_llm)
        SQL_LLM_string=str(SQL_llm)
        if check_gpt_4o(SQL_LLM_string):
            gpt4o_check=1
            #st.write("1111111111")
        if check_gpt_4o_mini(SQL_LLM_string):
            gpt4o_mini_check=1
            #st.write("222222222222")
    max_retries=9

    if db_name == "CC17":
        llm_context_prompt_template = """
        You are an SQLite expert. 
        Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.
        Never limit the number of results unless the user specifies a specific number.
        永遠不要限制結果數量，除非使用者明確指定了一個具體的數字。
        You can order the results to return the most informative data in the database.
        Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
        Pay attention to use TRUNC(SYSDATE) function to get the current date, if the question involves "today".
        Always ensure that the generated SQL query ends with a semicolon (;).
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
        User input: table CC17叫做大額費用明細表。、DP代表部門、ACCT表示會計科目、'6322EC'表示修護費用、AMT表示金額。在前述規則下，不限部門，請把'VOCHCSUMR'欄位中，有關"PA廠推高機輪胎龜裂"修護費用的資料一一列出來
        SQL query: SELECT DP, ACCT, AMT, VOCHCSUMR FROM CC17 WHERE ACCT = '6322EC' AND VOCHCSUMR LIKE '%PA廠推高機輪胎龜裂%';
        User input: CC17中ACCT=8003RZ的第一筆資料
        SQL query: SELECT * FROM CC17 WHERE ACCT = '8003RZ' LIMIT 1;


        Question: {input}   
        """
    if db_name == "netincome":
        llm_context_prompt_template = """
        You are an SQLite expert. 
        Given an input question, first create a syntactically correct SQLite query to run, then look at the results of the query and return the answer to the input question.
        Never limit the number of results unless the user specifies a specific number.
        永遠不要限制結果數量，除非使用者明確指定了一個具體的數字。
        You can order the results to return the most informative data in the database.
        Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
        Pay attention to use TRUNC(SYSDATE) function to get the current date, if the question involves "today".
        Always ensure that the generated SQL query ends with a semicolon (;).
        Use the following format:
        Question: Question here
        SQLQuery: SQL Query to run
        SQLResult: Result of the SQLQuery
        Answer: Final answer here
        Only use the following tables:
        {table_info} 
        Below are a number of examples of questions and their corresponding SQL queries:  
        User input: DTYM=202301的TARIFFAMT加起來
        SQL query: SELECT SUM(TARIFFAMT) AS 總金額 FROM netincome WHERE DTYM = '202301';
        User input: SALARE=荷蘭的TARIFFAMT總和
        SQL query: SELECT SUM(TARIFFAMT) AS 總金額 FROM netincome WHERE SALARE = '荷蘭';
        User input: 把有關ＵＰ樹脂的資料一一列出來
        SELECT * FROM netincome WHERE PDLCNM LIKE '%樹脂%';
        Question: {input}   
        """

    LLM_CONTEXT_PROMPT = PromptTemplate.from_template(llm_context_prompt_template)
    db = db_connection(db_name, db_source)
    
    # Get database context (table information)
    context = db.get_context()
    table_info = context["table_info"]
    #st.write("table_info",table_info)
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
    prompt = LLM_CONTEXT_PROMPT.format(input=query, table_info=table_info)
    check_validated_query_sql_query=0
    retries = 0
    response = None
    def fetch_query_result_with_headers(query, db_path):
        conn = sqlite3.connect(db_name+".db")
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        df = pd.DataFrame(result, columns=headers)
        return df
    def gpt_4o_extract_sql_query(string):
        # 使用正則表達式提取以 SELECT 開頭和 ; 結尾的部分
        pattern = r"(SELECT.*?;)"
        match = re.search(pattern, string, re.DOTALL | re.IGNORECASE)
        if match:
            # 返回找到的查詢語句
            return match.group(1)
        else:
            return None



    def return_valid_query(execute_result_sql_query, execute_result_validated_query,check_validated_query_sql_query):
        # 檢查字串是否非空且不含 'error' 和 'invalid'
        def is_valid(query):
            if query:
                return query and 'error' not in query.lower() and 'invalid' not in query.lower() and len(query)>0 and '[(none,)]' not in query.lower()
        
        # 優先回傳 execute_result2_validated_query
        if is_valid(execute_result_sql_query):
            check_validated_query_sql_query=1
            #st.write("11111111111111")
            return execute_result_sql_query,check_validated_query_sql_query
        elif is_valid(execute_result_validated_query):
            check_validated_query_sql_query=2
            #st.write("22222222222222")
            return execute_result_validated_query,check_validated_query_sql_query
        return None

    gpt_4o_extract_sql_query_check=0
    while retries <= max_retries:
        try:
            
            query_result = write_query.invoke({"question": prompt})
            sql_query = query_result  # 取得 SQL 查詢
            if gpt4o_check==1 or gpt4o_mini_check==1:
                #st.write("sql_query",sql_query)
                sql_query=gpt_4o_extract_sql_query(sql_query)
            if not sql_query.endswith(';'):
                sql_query += ';'
            #st.write("sql_query",sql_query)
            validated_query = validation_chain.invoke({"query": sql_query})
            #st.write("validated_query ",validated_query)
            validated_query=gpt_4o_extract_sql_query(validated_query)
            if not validated_query.endswith(';'):
                sql_query += ';'
            #st.write("validated_query ",validated_query)
 
            execute_result_sql_query = execute_query.invoke({"query": sql_query})
            execute_result_validated_query = execute_query.invoke({"query": validated_query})
            # Invoke the chain with the generated prompt
            #response = chain.invoke({"question": prompt})
            
            response_sql_query=execute_result_sql_query
            response_result_validated_query=execute_result_validated_query
            response_sql_query=str(response_sql_query)
            response_result_validated_query=str(response_result_validated_query)
            #st.write("execute_result_sql_query",execute_result_sql_query)
            #st.write("execute_result_validated_query",execute_result_validated_query)
            # Check if response contains invalid column name error
            response,check_validated_query_sql_query = return_valid_query(execute_result_sql_query,execute_result_validated_query,check_validated_query_sql_query)
            if response is not None :
                break  
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
    
    columns=[]
    #st.write("000000000000000000",check_validated_query_sql_query)
    if check_validated_query_sql_query==1 and len(response)>2 : 
        columns=fetch_query_result_with_headers(sql_query ,db)
    if check_validated_query_sql_query==2 and len(response)>2 :
        columns=fetch_query_result_with_headers(validated_query ,db)
        
    if columns.empty:
        st.write("None")
    else:
        columns_string=columns.to_string()
        if len(columns_string) <= 600:
            st.write("fetch_query_result_with_headers",columns)
        else:
            response = "內容過多，請下載csv查看"
            # 将 DataFrame 转换为 CSV 格式的字节流
            csv = columns.to_csv(index=False).encode('utf-8-sig')
            # 提供下载按钮
            st.download_button(
                label="下载结果CSV文件",
                data=csv,
                file_name='query_result.csv',
                mime='text/csv'
            )


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