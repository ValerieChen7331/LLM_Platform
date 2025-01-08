from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from apis.file_paths import FilePaths

class BaseDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self._ensure_db_path_exists()
        self._ensure_db_exists()

    def _ensure_db_path_exists(self):
        """確保資料庫文件夾存在。"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_db_exists(self):
        """檢查資料庫文件是否存在，不存在則初始化資料庫。"""
        if not self.db_path.exists():
            self._init_db()

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        raise NotImplementedError("子類別需要實現這個方法。")

    def execute_query(self, query, params=()):
        """執行資料庫的寫入操作。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(query, params)
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"資料庫操作錯誤: {e}")
            raise

    def fetch_query(self, query, params=()):
        """執行資料庫的查詢操作並返回結果。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(query, params)
                return c.fetchall()
        except sqlite3.OperationalError as e:
            print(f"資料庫操作錯誤: {e}")
            raise



class UserRecordsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        user_records_db_path = self.file_paths.get_user_records_dir().joinpath('UserRecordsDB.db')
        super().__init__(user_records_db_path)
        self.columns = [
            'id', 'agent', 'mode', 'model', 'api_base', 'api_key',
            'db_source', 'db_name',
            'conversation_id', 'active_window_index', 'num_chat_windows', 'title',
            'user_query', 'ai_response'
        ]

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                             (id INTEGER PRIMARY KEY,
                              agent TEXT,
                              mode TEXT, 
                              model TEXT, 
                              api_base TEXT, 
                              api_key TEXT,                             
                              db_source TEXT, 
                              db_name TEXT,                              
                              conversation_id TEXT, 
                              active_window_index INTEGER,,
                              num_chat_windows INTEGER,
                              title TEXT,                              
                              user_query TEXT, 
                              ai_response TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS pdf_uploads
                             (id INTEGER PRIMARY KEY, 
                              pdf_path TEXT, 
                              embeddings_path TEXT, 
                              upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                conn.commit()
            print("UserRecordsD 資料庫初始化成功。")
        except sqlite3.OperationalError as e:
            print(f"UserRecordsD 資料庫操作錯誤: {e}")
            raise

    def load_database(self):
        """載入聊天記錄，並以 DataFrame 格式返回。"""
        try:
            sql_query = f"SELECT {', '.join(self.columns)} FROM chat_history"
            data = self.fetch_query(sql_query)
            return pd.DataFrame(data, columns=self.columns) if data else pd.DataFrame(columns=self.columns)
        except Exception as e:
            print(f"load_database 發生錯誤: {e}")
            return pd.DataFrame(columns=self.columns)

    def get_chat_history(self):
        try:
            # 獲取當前的聊天窗口索引
            active_window_index = st.session_state.get('active_window_index')

            # 定義 SQL 查詢
            sql_query = """
            SELECT id, conversation_id, active_window_index, user_query, ai_response 
            FROM chat_history 
            WHERE active_window_index = ? 
            ORDER BY id
            """

            # 執行查詢並取得結果
            chat_history_database = self.fetch_query(sql_query, (active_window_index,))

            # 如果查詢結果為空，設定一個空列表
            if not chat_history_database:
                st.session_state['chat_history'] = []

            # 確保列數與查詢結果匹配，並轉換為字典列表
            columns = ['id', 'conversation_id', 'active_window_index', 'user_query', 'ai_response']
            current_chat_history = pd.DataFrame(chat_history_database, columns=columns).to_dict(orient='records')

            # 將當前的聊天記錄儲存到 session state 中
            st.session_state['chat_history'] = current_chat_history

        except Exception as e:
            print(f"get_chat_history 發生錯誤: {e}")
            st.session_state['chat_history'] = []

    def save_to_database(self, query, response):
        """將查詢結果保存到資料庫中。"""
        agent = st.session_state.get('agent')

        mode = st.session_state.get('mode')
        model = st.session_state.get('model')
        api_base = st.session_state.get('api_base')
        api_key = st.session_state.get('api_key')

        # sql model

        db_source = st.session_state.get('db_source')
        db_name = st.session_state.get('db_name')

        conversation_id = st.session_state.get('conversation_id')
        active_window_index = st.session_state.get('active_window_index')
        num_chat_windows = st.session_state.get('num_chat_windows')
        title = st.session_state.get('title')

        # retriever

        self.execute_query(
            """
            INSERT INTO chat_history 
            (agent, mode, model, api_base, api_key, 
            db_source, db_name,
            conversation_id, active_window_index, num_chat_windows, title,
            user_query, ai_response) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent, mode, model, api_base, api_key,
                db_source, db_name,
                conversation_id, active_window_index, num_chat_windows, title,
                query, response
            )
        )

class DevOpsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        dev_ops_db_path = self.file_paths.get_devOps_dir().joinpath('DevOpsDB.db')
        super().__init__(dev_ops_db_path)

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                             (id INTEGER PRIMARY KEY,
                             
                              user TEXT,
                              upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              
                              agent TEXT,
                              mode TEXT, 
                              model TEXT, 
                              api_base TEXT, 
                              api_key TEXT,                             
                              db_source TEXT, 
                              db_name TEXT,                              
                              conversation_id TEXT, 
                              active_window_index INTEGER,,
                              num_chat_windows INTEGER,
                              title TEXT,                              
                              user_query TEXT, 
                              ai_response TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS pdf_uploads
                             (id INTEGER PRIMARY KEY, 
                              pdf_path TEXT, 
                              embeddings_path TEXT, 
                              upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                conn.commit()
            print("DevOpsDB 資料庫初始化成功。")
        except sqlite3.OperationalError as e:
            print(f"DevOpsDB 資料庫操作錯誤: {e}")
            raise

        def save_to_database(self, query, response):
            """將查詢結果保存到資料庫中。"""
            agent = st.session_state.get('agent')

            mode = st.session_state.get('mode')
            model = st.session_state.get('model')
            api_base = st.session_state.get('api_base')
            api_key = st.session_state.get('api_key')

            # sql model

            db_source = st.session_state.get('db_source')
            db_name = st.session_state.get('db_name')

            conversation_id = st.session_state.get('conversation_id')
            active_window_index = st.session_state.get('active_window_index')
            num_chat_windows = st.session_state.get('num_chat_windows')
            title = st.session_state.get('title')

            user =
            upload_time =


            # retriever

            self.execute_query(
                """
                INSERT INTO chat_history 
                (user,agent, mode, model, api_base, api_key, 
                db_source, db_name,
                conversation_id, active_window_index, num_chat_windows, title,
                user_query, ai_response) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent, mode, model, api_base, api_key,
                    db_source, db_name,
                    conversation_id, active_window_index, num_chat_windows, title,
                    query, response
                )
            )




