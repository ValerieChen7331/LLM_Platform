import streamlit as st
from models.llm_model import LLMModel
from models.database_model import UserRecordsDB
from models.database_model import DevOpsDB

class LLMService:
    def __init__(self):
        # 初始化 LLMModel 和 DatabaseModel
        self.llm_model = LLMModel()
        self.user_records_db = UserRecordsDB()
        self.devOps_db = DevOpsDB()

    def query(self, query):
        """根據查詢和可用的檢索器執行適當的 LLM 查詢。"""
        retriever = st.session_state.get('retriever')

        if retriever:
            # 使用檢索增強生成模式進行查詢
            response, retrieved_data = self.llm_model.query_llm_rag(retriever, query)
        else:
            # 直接使用 LLM 進行查詢
            response = self.llm_model.query_llm_direct(query)

        #--------------------
        if not st.session_state['chat_history']:
            st.session_state['title'] = self.llm_model.set_window_title(query)

        self.user_records_db.save_to_database(query, response)
        self.devOps_db.save_to_database(query, response)

        return response


