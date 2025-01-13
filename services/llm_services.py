import streamlit as st

from models.llm_model import LLMModel
from models.llm_rag import RAGModel
from models.database_userRecords import UserRecordsDB
from models.database_devOps import DevOpsDB

# from sql.sqlagent import agent
# from sql.sqlagent2 import agent as agent_II
# from sql.sql_test import query as qu


class LLMService:
    def __init__(self, chat_session_data):
        """初始化 LLMModel 和 DatabaseModel"""
        self.chat_session_data = chat_session_data
        self.llm_model = LLMModel(self.chat_session_data)
        self.llm_rag = RAGModel(self.chat_session_data)
        self.userRecords_db = UserRecordsDB(self.chat_session_data)
        self.devOps_db = DevOpsDB(self.chat_session_data)



    def query(self, query):
        """根據查詢和選擇的助理類型執行適當的 LLM 查詢"""
        # 從 session_state 取得相關設定

        selected_agent = self.chat_session_data.get('agent')
        db_name = self.chat_session_data.get('db_name')
        db_source = self.chat_session_data.get('db_source')

        # 如果聊天記錄為空，設定新窗口的標題
        if not self.chat_session_data.get('chat_history'):
            self.llm_model.set_window_title(query)

        # 根據選擇的助理類型來執行對應的查詢
        if selected_agent == '資料庫查找助理':
            # response = agent(query, db_name, db_source)
            response = ''
            print('資料庫查找助理...')

        elif selected_agent == '資料庫查找助理2.0':
            # response = agent_II(query, db_name, db_source)
            response = ''
            print('資料庫查找助理2.0...')

        elif selected_agent == 'SQL生成助理':
            # response = qu(query, db_name, db_source)
            response = ''
            print('SQL生成助理...')

        elif selected_agent == '個人KM':
            # 使用檢索增強生成模式進行查詢
            response, retrieved_data = self.llm_rag.query_llm_rag(query)

        else:
            # 直接使用 LLM 進行查詢
            response = self.llm_model.query_llm_direct(query)

        # 更新 session_state 中的聊天記錄
        self.chat_session_data['chat_history'].append({"user_query": query, "ai_response": response})
        self.chat_session_data['empty_window_exists'] = False

        # 將查詢和回應結果保存到資料庫
        self.userRecords_db.save_to_database(query, response)
        self.devOps_db.save_to_database(query, response)

        return response, self.chat_session_data
