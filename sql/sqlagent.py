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

def agent(query, db_name, db_source):
    # MSSQL DB
    db = db_connection(db_name, db_source)

    # SQL_LLM
    openai_api_base = 'http://10.5.61.81:11433/v1'
    model = "codeqwen"
    SQL_llm = llm(model, openai_api_base)

    # CHAT_LLM(With tool training)
    chat_model = "wangshenzhi/llama3.1_8b_chinese_chat"
    chat = llm(chat_model, openai_api_base)

    # 初始化或使用已存在的向量資料庫
    vector_db = initialize_vector_db(db)
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})
    
    description = """Use to look up values to filter on. Input is an approximate spelling of the proper noun, output is \
    valid proper nouns. Use the noun most similar to the search."""
    retriever_tool = create_retriever_tool(
        retriever,
        name="search_proper_nouns",
        description=description,
    )

    system = """You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    You have access to tools for interacting with the database.
    Only use the given tools. Only use the information returned by the tools to construct your final answer.
    You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    You have access to the following tables: {table_names}

    If you need to filter on a proper noun, you must ALWAYS first look up the filter value using the "search_proper_nouns" tool!
    Do not try to guess at the proper name - use this function to find similar ones.""".format(
        table_names=db.get_usable_table_names()
    )

    system_message = SystemMessage(content=system)
    
    # TOOLKIT
    toolkit = SQLDatabaseToolkit(db=db, llm=SQL_llm)
    tools = toolkit.get_tools()
    tools.append(retriever_tool)

    # Agent
    agent_executor = create_react_agent(chat, tools, state_modifier=system_message)

    # 結果
    contents = list(agent_executor.stream({"messages": [HumanMessage(content=query)]}))
    #return contents[-1]['agent']['messages'][0].content
    return retriever_tool.invoke("PA廠推高機輪胎龜裂")

