import streamlit as st
from models.llm_model import LLMModel
from models.database_model import DatabaseModel

class LLMService:
    def __init__(self):
        # 初始化 LLMModel
        self.llm_model = LLMModel()
        self.database_model = DatabaseModel()

    def query(self, query):
        # 從 session_state 獲取 retriever、model、api_base 和 api_key
        retriever = st.session_state.get('retriever')

        # 如果 retriever 存在，則使用檢索增強生成模式進行查詢
        if retriever:
            response, retrieved_data = self.llm_model.query_llm_rag(retriever, query)
        else:
            # 否則，直接使用 LLM 進行查詢
            response = self.llm_model.query_llm_direct(query)
        # 儲存消息和聊天歷史
        #st.session_state['messages'].append((query, response))
        #st.session_state['chat_history'].append(f"User: {query}")
        #st.session_state['chat_history'].append(f"AI: {response}")

        return response

    def title(self, query):
        # 檢查 chat_history 是否為空
        if not st.session_state['chat_history']:
            # 如果 chat_history 為空，使用 llm_model 來設置窗口標題
            st.session_state['title'] = self.llm_model.set_window_title(query)
        else:
            pass
        return
