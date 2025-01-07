from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from apis.file_paths import FilePaths


class DatabaseModel:
    def __init__(self):
        # 初始化資料庫路徑並建立資料庫
        self.file_paths = FilePaths()
        self.user_records_dir = self.file_paths.get_user_records_dir()
        self.get_devOps_dir = self.file_paths.get_devOps_dir()

        self.user_records_db_path = self.user_records_dir.joinpath('UserRecordsDB.db')
        self.devOps_db_path = self.get_devOps_dir.joinpath('DevOpsDB.db')

        self._ensure_db_path_exists()
        self._ensure_db_exists()

        # 定義聊天記錄表的列名
        self.columns = [
            'id', 'conversation_id', 'mode', 'model',
            'chat_window_index', 'user_query',
            'ai_response', 'title'
        ]

    def _ensure_db_path_exists(self):
        """確保資料庫文件夾存在。"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_db_exists(self):
        """檢查資料庫文件是否存在，不存在則初始化資料庫。"""
        if not self.db_path.exists():
            self._init_db()

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # 創建聊天記錄表格
                c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                             (id INTEGER PRIMARY KEY, 
                              conversation_id TEXT, 
                              mode TEXT, 
                              model TEXT, 
                              chat_window_index INTEGER, 
                              user_query TEXT, 
                              ai_response TEXT, 
                              title TEXT)''')
                # 創建PDF上傳記錄表格
                c.execute('''CREATE TABLE IF NOT EXISTS pdf_uploads
                             (id INTEGER PRIMARY KEY, 
                              pdf_path TEXT, 
                              embeddings_path TEXT, 
                              upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                conn.commit()
            print("資料庫初始化成功。")
        except sqlite3.OperationalError as e:
            print(f"資料庫操作錯誤: {e}")
            raise

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

    def load_database(self):
        """載入聊天記錄，並以 DataFrame 格式返回。"""
        try:
            sql_query = f"SELECT {', '.join(self.columns)} FROM chat_history"
            data = self.fetch_query(sql_query)

            return pd.DataFrame(data, columns=self.columns) if data else pd.DataFrame(columns=self.columns)
        except Exception as e:
            print(f"發生錯誤: {e}")
            return pd.DataFrame(columns=self.columns)

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
            chat_history_database = self.fetch_query(sql_query, (current_chat_window_index,))

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

        except Exception as e:
            # 處理其他錯誤
            print(f"發生錯誤: {e}")

    def save_to_database(self, query, response):
        """將查詢結果保存到資料庫中。"""
        mode = st.session_state['mode']
        model = st.session_state['model']
        current_chat_window_index = st.session_state['current_chat_window_index']
        title = st.session_state['title']

        self.execute_query(
            """
            INSERT INTO chat_history 
            (conversation_id, mode, model, chat_window_index, user_query, ai_response, title) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                st.session_state['conversation_id'], mode, model,
                current_chat_window_index, query, response, title
            )
        )
