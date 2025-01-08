from services.llm_services import LLMService
from services.document_services import DocumentService
from models.batabase_userRecords import UserRecordsDB
import streamlit as st
import uuid
import pandas as pd
import sqlite3

class UIController:
    def __init__(self):
        # 初始化 LLMService 和 DocumentService
        self.llm_service = LLMService()
        self.doc_service = DocumentService()
        self.userRecords_db = UserRecordsDB()

    def initialize_session_state(self):
        # 從 userRecords_db 載入資料
        database = self.userRecords_db.load_database()

        # 設置聊天窗口的數量及活躍窗口索引
        if not database.empty:
            count_chat_windows = len(set(database['active_window_index']))
            active_window_index = count_chat_windows
            count_chat_windows += 1
        else:
            count_chat_windows = 1
            active_window_index = 0

        st.session_state.setdefault('num_chat_windows', count_chat_windows)
        st.session_state.setdefault('active_window_index', active_window_index)
        print('----------------')
        print('num_chat_windows')
        print(st.session_state['num_chat_windows'])
        print('active_window_index')
        print( st.session_state['active_window_index'])
        print('----------------')

        # 初始化其他 session 狀態參數
        default_session_params = {
            'mode': '內部LLM',
            'model': None,
            'option': None,
            'messages': [],
            'retriever': None,
            'api_base': None,
            'api_key': None,
            'conversation_id': str(uuid.uuid4()),
            'chat_history': [],
            'title': '',
            'agent': '一般助理',
            'db_name': None,
            'db_source': None,
        }

        for key, value in default_session_params.items():
            st.session_state.setdefault(key, value)

    def get_title(self, index):
        # 從資料庫加載數據
        df_database = self.userRecords_db.load_database()  # 使用 userRecords_db 而非 database_model

        # 過濾出匹配 active_window_index 的行
        df_window = df_database[df_database['active_window_index'] == index]

        # 如果找到匹配的行，將標題設置到 session state 中
        if not df_window.empty:
            title = df_window['title'].iloc[0]
        else:
            # 若未找到匹配的行，設置默認標題
            title = "(新對話)"
        return title

    def new_chat(self):
        # 創建新聊天窗口，更新 session 狀態
        if st.session_state.get('chat_history'):
            st.session_state['conversation_id'] = str(uuid.uuid4())
            st.session_state['chat_history'] = []
            st.session_state['num_chat_windows'] += 1
            st.session_state['active_window_index'] = st.session_state['num_chat_windows']
            st.session_state['retriever'] = None
            st.rerun()  # 刷新頁面

    def delete_chat_history_and_update_indexes(self, delete_index):
        # 刪除指定聊天窗口索引的聊天歷史記錄
        self.userRecords_db.execute_query(  # 使用 userRecords_db 而非 database_model
            "DELETE FROM chat_history WHERE active_window_index = ?", (delete_index,))

        # 更新剩餘聊天窗口的索引
        chat_histories = self.userRecords_db.fetch_query(  # 使用 userRecords_db 而非 database_model
            "SELECT id, active_window_index FROM chat_history ORDER BY active_window_index")

        for id, active_window_index in chat_histories:
            if active_window_index > delete_index:
                new_index = active_window_index - 1
                self.userRecords_db.execute_query(  # 使用 userRecords_db 而非 database_model
                    "UPDATE chat_history SET active_window_index = ? WHERE id = ?", (new_index, id))

        # 更新 session state 中的聊天窗口索引
        st.session_state['num_chat_windows'] -= 1

    def handle_query(self, query):
        # 處理使用者查詢，發送給 LLM 並顯示回應
        st.chat_message("human").write(query)
        response = self.llm_service.query(query)
        st.chat_message("ai").write(response)

    def process_uploaded_documents(self):
        # 處理上傳的文件
        self.doc_service.process_uploaded_documents()
