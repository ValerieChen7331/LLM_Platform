import streamlit as st
from datetime import datetime
from models.batabase_base import BaseDB
from apis.file_paths import FilePaths

class DevOpsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        db_path = self.file_paths.get_devOps_dir().joinpath('DevOpsDB.db')
        super().__init__(db_path)

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        chat_history_query = '''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                user TEXT,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                agent TEXT, 
                mode TEXT, 
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

        pdf_uploads_query = '''
            CREATE TABLE IF NOT EXISTS pdf_uploads (
                id INTEGER PRIMARY KEY,
                pdf_path TEXT, 
                embeddings_path TEXT,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.execute_query(pdf_uploads_query)
        print("DevOpsDB 資料庫初始化成功。")

    def save_to_database(self, query: str, response: str):
        """將查詢結果保存到資料庫中。"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 取得當前時間

        data = {
            # UserDB 中沒有
            'user': st.session_state.get('username'),   # 添加使用者帳號
            'upload_time': current_time,    # 添加當前時間到數據中
            # UserDB 也有
            'agent': st.session_state.get('agent', ''),
            'mode': st.session_state.get('mode', ''),
            'model': st.session_state.get('model', ''),

            'db_source': st.session_state.get('db_source', ''),
            'db_name': st.session_state.get('db_name', ''),
            'conversation_id': st.session_state.get('conversation_id', ''),
            'active_window_index': st.session_state.get('active_window_index', 0),
            'num_chat_windows': st.session_state.get('num_chat_windows', 0),
            'title': st.session_state.get('title', ''),
            'user_query': query,
            'ai_response': response
        }

        try:
            self.execute_query(
                """
                INSERT INTO chat_history 
                (user, upload_time, agent, mode, model, db_source, db_name,
                 conversation_id, active_window_index, num_chat_windows, title,
                 user_query, ai_response) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            print("Data successfully saved to DevOpsDB.")
        except Exception as e:
            print(f"An error occurred while saving to the DevOpsDB: {e}")
