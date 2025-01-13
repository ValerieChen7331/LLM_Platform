from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.exc import OperationalError

from sql.db_connection import db_connection
from sql.llm import llm

import streamlit as st
from apis.llm_api import LLMAPI

class SQLAgentII:
    def __init__(self, chat_session_data):
        self.chat_session_data = chat_session_data

    def llm_sql(self):
        mode = self.chat_session_data.get('mode')
        if mode == '內部LLM':
            # SQL_LLM
            openai_api_base = 'http://10.5.61.81:11433/v1'
            # model ="sqlcoder:15b"
            # model ="deepseek-coder-v2"
            model ="duckdb-nsql"
            # model ="codeqwen"
            SQL_llm = llm(model,openai_api_base)

            # 為了DB紀錄
            self.chat_session_data['model'] = model

            # CHAT_LLM(With tool training)
            openai_api_base = 'http://10.5.61.81:11433/v1'
            model ="wangshenzhi/llama3.1_8b_chinese_chat"
            chat = llm(model,openai_api_base)

        else:
            llm_option = self.chat_session_data.get('llm_option')
            SQL_llm = LLMAPI.get_llm(mode, llm_option)
            chat = LLMAPI.get_llm(mode, llm_option)

        return SQL_llm, chat

    def get_db_schema(db):
        # print(db.get_table_info())
        return db.get_table_info()

    def run_query(query, db):
        try:
            print(query)
            return db.run(query)
        except (OperationalError, Exception) as e:
            return str(e)

    def agent(self, question):
        db_name = self.chat_session_data.get('db_name')
        db_source = self.chat_session_data.get('db_source')
        SQL_llm, chat = self.llm_sql()

        # 建立資料庫連線
        db = db_connection(db_name,db_source)

        # 設置 SQL 生成鏈
        gen_sql_prompt = ChatPromptTemplate.from_messages([
        ('system', 'To start you should ALWAYS look at the table schema : {db_schema} in the database to see what you can query.'),
        ('user', 'Please generate a SQL query refer to {db_schema} for the following question: "{input}". \
         USE TIMESTAMP INSTEAD OF time or date \
         The query should be formatted as follows without any additional explanation: \
         SQL> <sql_query>\
        '),
        ])

        gen_query_chain = (
            RunnablePassthrough.assign(db_schema=self.get_db_schema(db))
            | gen_sql_prompt
            | SQL_llm
            | StrOutputParser()
        )


        gen_answer_prompt = ChatPromptTemplate.from_template("""
        Based on the provided question, SQL query, and query result, write a natural language response including column name.
        No additional explanations should be included.
    
        Question: {input}
        SQL Query: {query}
        Query Result: {result}
    
        The response should be formatted as follows:
        '''
        Executed: {query}
        Answer: <answer>
        '''
        """)


        chain = (
            RunnablePassthrough.assign(query=gen_query_chain).assign(
                result=lambda x: self.run_query(x["query"],db),
            )
            | gen_answer_prompt
            | chat
        )

        # 執行操作鏈
        response = chain.invoke({'input': question})

        return response



# print(db.dialect)
# print(db.get_usable_table_names())
# print(db.run("SELECT * FROM Artist LIMIT 10;"))




# Result
# print(db.run(response))

# Another method

# from operator import itemgetter
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.prompts import PromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

# execute_query = QuerySQLDataBaseTool(db=db)
# write_query = create_sql_query_chain(llm, db)

# answer_prompt = PromptTemplate.from_template(
#     """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

# Question: {question}
# SQL Query: {query}
# SQL Result: {result}
# Answer: """
# )

# chain = (
#     RunnablePassthrough.assign(query=write_query).assign(
#         result=itemgetter("query") | execute_query
#     )
#     | answer_prompt
#     | llm2
#     | StrOutputParser()
# )

# response =chain.invoke({"question": "How many employees are there"})
# print(response)