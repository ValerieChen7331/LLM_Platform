from services.llm_services import LLMService
from services.document_services import DocumentService
from models.database_model import DatabaseModel
import streamlit as st
import uuid
import pandas as pd
import sqlite3

class UIController:
    def __init__(self):
        # 初始化 LLMService 和 DocumentService
        self.llm_service = LLMService()
        self.doc_service = DocumentService()
        self.database_model = DatabaseModel()

    def initialize_session_state(self):
        # 初始化 session 狀態
        database = self.database_model.load_database()

        if not database.empty:
            # 計算聊天窗口的數量並設置 session state
            count_chat_windows = len(set(database['chat_window_index']))
            st.session_state.setdefault('chat_window_index', count_chat_windows)
            st.session_state.setdefault('current_chat_window_index', count_chat_windows)
        else:
            # 沒有歷史記錄時初始化為 0
            st.session_state.setdefault('chat_window_index', 0)
            st.session_state.setdefault('current_chat_window_index', 0)

        # 初始化其他 session 狀態參數
        st.session_state.setdefault('mode', '內部LLM')
        st.session_state.setdefault('model', None)
        st.session_state.setdefault('option', None)
        st.session_state.setdefault('messages', [])
        st.session_state.setdefault('retriever', None)
        st.session_state.setdefault('api_base', None)
        st.session_state.setdefault('api_key', None)
        st.session_state.setdefault('current_model', None)
        st.session_state.setdefault('conversation_id', str(uuid.uuid4()))
        st.session_state.setdefault('chat_history', [])
        st.session_state.setdefault('title', '')

    def get_title(self, current_chat_window_index):
        # 從資料庫加載數據
        df_database = self.database_model.load_database()

        # 過濾出匹配 current_chat_window_index 的行
        df_window = df_database[df_database['chat_window_index'] == current_chat_window_index]

        # 如果找到匹配的行，將標題設置到 session state 中
        if not df_window.empty:
            title = df_window['title'].iloc[0]
        else:
            # 若未找到匹配的行，設置默認標題
            title = f"(新對話)"
        return title

    def new_chat(self):
        # 創建新聊天窗口，更新 session 狀態
        st.session_state['conversation_id'] = str(uuid.uuid4())
        st.session_state['chat_history'] = []
        st.session_state['chat_window_index'] += 1
        st.session_state['current_chat_window_index'] = st.session_state['chat_window_index']



    def delete_chat_history_and_update_indexes(self, delete_index):
        # 刪除指定聊天窗口索引的聊天歷史記錄
        self.database_model.execute_query(
            "DELETE FROM chat_history WHERE chat_window_index = ?", (delete_index,))

        # 更新剩餘聊天窗口的索引
        chat_histories = self.database_model.fetch_query(
            "SELECT id, chat_window_index FROM chat_history ORDER BY chat_window_index")

        for id, chat_window_index in chat_histories:
            if chat_window_index > delete_index:
                new_index = chat_window_index - 1
                self.database_model.execute_query(
                    "UPDATE chat_history SET chat_window_index = ? WHERE id = ?", (new_index, id))

        # 更新 session state 中的聊天窗口索引
        st.session_state['chat_window_index'] -= 1

    def handle_query(self, query):
        # 處理使用者查詢，發送給 LLM 並顯示回應
        st.chat_message("human").write(query)
        response = self.llm_service.query(query)
        st.chat_message("ai").write(response)


    def process_uploaded_documents(self):
        # 處理上傳的文件
        self.doc_service.process_uploaded_documents()
