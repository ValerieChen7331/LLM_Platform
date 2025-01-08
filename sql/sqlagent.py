from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from sql.db_connection import db_connection
from sql.llm import llm

def agent(query,db_name,db_source):
    # MSSQL DB
    db = db_connection(db_name,db_source)

    # SQL_LLM
    openai_api_base = 'http://10.5.61.81:11433/v1'
    # model ="sqlcoder"
    # model ="deepseek-coder-v2"
    model ="duckdb-nsql"
    # model ="codeqwen"
    SQL_llm = llm(model,openai_api_base)

    # CHAT_LLM(With tool training)
    openai_api_base = 'http://10.5.61.81:11433/v1'
    model ="wangshenzhi/llama3.1_8b_chinese_chat"
    chat = llm(model,openai_api_base)

    # TOOLKIT
    toolkit = SQLDatabaseToolkit(db=db, llm=SQL_llm)
    tools = toolkit.get_tools()

    # PROMPT
    with open('sql/prompt.md', 'r') as file:
        SQL_PREFIX = file.read()

    system_message = SystemMessage(content=SQL_PREFIX)

    # Agent
    agent_executor = create_react_agent(chat, tools, state_modifier=system_message)

    # Result
    # for s in agent_executor.stream({"messages": [HumanMessage(content="anomalyRecords on 2023-10-10 10:40:01.000")]}):
    #     print(s)
    #     print("----")
    contents= list(agent_executor.stream({"messages": [HumanMessage(content=query)]}))
    return contents[-1]['agent']['messages'][0].content
# print(agent("anomalyRecords on 2023-10-10 10:40:01.000"))
# netincome table, 尋找CUNO=JPRAQY, DTYM=11306的Salqty