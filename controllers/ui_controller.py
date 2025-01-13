#from services.llm_services import LLMService
# from services.document_services import DocumentService
from models.database_userRecords import UserRecordsDB

import uuid
# import pandas as pd
# import os
# import streamlit as st

class UIController:
    def __init__(self):
        # 初始化 LLMService 和 DocumentService
        #self.llm_service = LLMService()
        #self.doc_service = DocumentService()
        # 初始化 UserRecordsDB
        self.userRecords_db = UserRecordsDB(chat_session_data={})  # 先以空字典初始化
        # 初始化 Session 狀態
        self.chat_session_data = self.initialize_session_state()
        # 更新 UserRecordsDB 的 chat_session_data
        self.userRecords_db.chat_session_data = self.chat_session_data

    def initialize_session_state(self):
        """初始化 Session 狀態，並儲存到字典 chat_session_data"""
        # 從 userRecords_db 載入資料，只取 active_window_index 欄位
        database = self.userRecords_db.load_database('chat_history', ['active_window_index'])

        # 設置聊天窗口的數量及活躍窗口索引
        count_chat_windows = len(set(database['active_window_index'])) if not database.empty else 0
        active_window_index = count_chat_windows
        count_chat_windows += 1

        # 初始化 session 狀態參數，並儲存到字典 chat_session_data
        chat_session_data = {
            'conversation_id': str(uuid.uuid4()),  # 新的對話 ID
            'num_chat_windows': count_chat_windows,
            'active_window_index': active_window_index,
            'agent': '一般助理',
            'mode': '內部LLM',
            'llm_option': 'Qwen2-Alibaba',
            'model': 'qwen2:7b',
            'api_base': '',
            'api_key': '',
            'embedding': 'llama3',
            'doc_names': '',
            'db_name': '',
            'db_source': '',
            'chat_history': [],
            'title': '',

            'upload_time': None,
            'username': None,

            'empty_window_exists': True  # 確保新窗口存在
        }
        return chat_session_data

    def get_title(self, index):
        """根據窗口索引返回標題"""
        # 從資料庫加載數據
        df_database = self.userRecords_db.load_database(
            'chat_history',
            ['active_window_index', 'title'])
        df_window = df_database[df_database['active_window_index'] == index]

        # 設置標題，如果無數據則為新對話
        if not df_window.empty:
            window_title = df_window['title'].iloc[0]
        else:
            window_title = "(新對話)"
        return window_title

    def new_chat(self, chat_session_data):
        """創建新聊天窗口，更新 chat_session_data 狀態"""
        if chat_session_data.get('empty_window_exists'):
            chat_session_data['active_window_index'] = chat_session_data.get('num_chat_windows') - 1
        else:
            chat_session_data['active_window_index'] = chat_session_data.get('num_chat_windows')
            chat_session_data['num_chat_windows'] += 1

        chat_session_data['conversation_id'] = str(uuid.uuid4())
        chat_session_data = self.userRecords_db.reset_session_state_to_defaults()
        chat_session_data['empty_window_exists'] = True

        return chat_session_data

    def delete_chat_history_and_update_indexes(self, delete_index, chat_session_data):
        """刪除指定聊天窗口並更新索引"""
        # 刪除指定聊天窗口索引的聊天歷史記錄
        self.userRecords_db.delete_chat_by_index(delete_index)
        # 更新剩餘聊天窗口的索引
        self.userRecords_db.update_chat_indexes(delete_index)
        # 更新聊天窗口的數量
        chat_session_data['num_chat_windows'] -= 1
        return chat_session_data

    # def handle_query(self, query):
    #     """處理使用者查詢，並獲取回應"""
    #     st.chat_message("human").write(query)
    #     response = self.llm_service.query(query)
    #     st.chat_message("ai").write(response)
    #
    # def process_uploaded_documents(self):
    #     """處理上傳的文件"""
    #     self.doc_service.process_uploaded_documents()
