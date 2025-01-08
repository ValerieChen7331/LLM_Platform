import streamlit as st
from datetime import datetime
from models.batabase_base import BaseDB
from apis.file_paths import FilePaths
import logging

logging.basicConfig(level=logging.INFO)

class DevOpsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        db_path = self.file_paths.get_devOps_dir().joinpath('DevOpsDB.db')
        super().__init__(db_path)

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""

        # 建立 chat_history 表格
        chat_history_query = '''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- DevOpsDB 增加，UserRecordsDB 沒有
                username TEXT,                                        -- DevOpsDB 增加，UserRecordsDB 沒有
                agent TEXT,
                mode TEXT,
                llm_option TEXT,
                model TEXT,
                db_source TEXT,
                db_name TEXT,
                conversation_id TEXT,
                active_window_index INTEGER,
                num_chat_windows INTEGER,
                title TEXT,
                user_query TEXT,
                ai_response TEXT
            )
        '''
        self.execute_query(chat_history_query)

        # 建立 pdf_uploads 表格
        pdf_uploads_query = '''
            CREATE TABLE IF NOT EXISTS pdf_uploads (
                id INTEGER PRIMARY KEY,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- UserRecordsDB 沒有
                username TEXT,                                        -- UserRecordsDB 沒有
                conversation_id TEXT,
                agent TEXT,
                embedding TEXT,
                doc_names TEXT
            )
        '''
        self.execute_query(pdf_uploads_query)
        logging.info("DevOpsDB 資料庫初始化成功。")

    def save_to_database(self, query: str, response: str):
        """將查詢結果保存到資料庫中。"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 取得當前時間

        # 初始化 data 字典，從 session_state 中獲取數據
        data = {key: st.session_state.get(key, default) for key, default in {
            # DevOpsDB 增加，UserRecordsDB 沒有
            'upload_time': current_time,
            'username': '',
            # UserRecordsDB 也有
            'agent': '',
            'mode': '',
            'llm_option': '',
            'model': '',
            'db_source': '',
            'db_name': '',
            'conversation_id': '',
            'active_window_index': 0,
            'num_chat_windows': 0,
            'title': '',
            'user_query': query,
            'ai_response': response,
        }.items()}

        try:
            self.execute_query(
                """
                INSERT INTO chat_history 
                (upload_time, username, agent, mode, llm_option, model, db_source, db_name,
                 conversation_id, active_window_index, num_chat_windows, title,
                 user_query, ai_response) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            logging.info("查詢結果已成功保存到資料庫 DevOpsDB (chat_history)")
        except Exception as e:
            logging.error(f"保存到 DevOpsDB (chat_history) 資料庫時發生錯誤: {e}")

    def save_to_pdf_uploads(self):
        """將查詢結果保存到資料庫中。"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 取得當前時間

        # 初始化 data 字典，從 session_state 中獲取數據
        data = {key: st.session_state.get(key, default) for key, default in {
            'upload_time': current_time,
            'username': '',
            'conversation_id': '',
            'agent': '',
            'embedding': '',
            'doc_names': ''
        }.items()}

        try:
            # 插入資料
            self.execute_query(
                """
                INSERT INTO pdf_uploads 
                (upload_time, username, conversation_id, agent, embedding, doc_names ) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            logging.info("查詢結果已成功保存到資料庫 DevOpsDB (pdf_uploads)。")
        except Exception as e:
            # 記錄錯誤訊息
            logging.error(f"保存到 DevOpsDB (pdf_uploads) 資料庫時發生錯誤: {e}")
