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
        check_history = not database.empty

        if check_history:
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

        return check_history

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

    def get_chat_history(self):
        try:
            # 獲取當前聊天窗口索引
            current_chat_window_index = st.session_state.get('current_chat_window_index')

            if current_chat_window_index is None:
                # 如果沒有當前聊天窗口索引，清空並返回空的聊天歷史記錄
                st.session_state['chat_history'] = []
                return []

            # SQL 查詢，根據當前聊天窗口索引查找聊天歷史記錄
            sql_query = """
            SELECT id, conversation_id, chat_window_index, user_query, ai_response 
            FROM chat_history 
            WHERE chat_window_index = ? 
            ORDER BY id
            """
            chat_history_database = self.database_model.fetch_query(sql_query, (current_chat_window_index,))

            # 檢查是否有資料返回
            if chat_history_database:
                # 將資料轉換為 DataFrame
                df = pd.DataFrame(chat_history_database,
                                  columns=['id', 'conversation_id', 'chat_window_index', 'user_query', 'ai_response'])

                # 將當前聊天視窗索引和聊天歷史記錄儲存到 session state 中
                current_chat_history = df[['user_query', 'ai_response']].values.tolist()
            else:
                # 如果沒有資料返回，設置空的聊天歷史記錄
                current_chat_history = []

            # 更新 session state 並返回聊天歷史記錄
            st.session_state['chat_history'] = current_chat_history
            return current_chat_history

        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
        except Exception as e:
            # 處理其他錯誤
            print(f"發生錯誤: {e}")

        # 返回空的聊天歷史記錄作為錯誤處理的一部分
        return []

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
