from langchain.chains import create_sql_query_chain

from sql.db_connection import db_connection
from sql.llm import llm

import streamlit as st
from apis.llm_api import LLMAPI


def query(question,db_name,db_source):
    # MSSQL DB
    db = db_connection(db_name,db_source)
    # print(db.dialect)
    # print(db.get_usable_table_names())
    # print(db.run("SELECT * FROM Artist LIMIT 10;"))

    if st.session_state.get('mode') == '內部LLM':
        # SQL_LLM
        openai_api_base = 'http://10.5.61.81:11433/v1'
        # model ="sqlcoder"
        # model ="deepseek-coder-v2"
        model ="duckdb-nsql"
        # model ="codeqwen"
        SQL_llm = llm(model,openai_api_base)

        # 為了DB紀錄
        st.session_state['model'] = model
    else:
        SQL_llm = LLMAPI.get_llm()

    # Chain
    chain = create_sql_query_chain(SQL_llm, db)

    # Get Prompt
    print(chain.get_prompts()[0].pretty_print())

    # AI's SQL 
    # question = "anomalyRecords on 2023-10-10 10:40:01.000"
    response = chain.invoke({"question": question})
    # print(response)
    return response

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