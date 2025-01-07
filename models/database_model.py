from pathlib import Path
import sqlite3
import streamlit as st
import pandas as pd

class DatabaseModel:
    def __init__(self):
        # 初始化資料庫路徑並建立資料庫
        self.db_path = Path(__file__).resolve().parent.parent.joinpath('data', 'chat_history.db')
        self.ensure_db_path_exists()
        self.ensure_db_exists()

    def ensure_db_exists(self):
        # 檢查資料庫文件是否存在
        if not self.db_path.exists():
            self.init_db()

    def ensure_db_path_exists(self):
        # 確保資料夾存在
        db_dir = self.db_path.parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_db(self):
        # 初始化資料庫
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                # 建立聊天記錄表格
                c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                             (id INTEGER PRIMARY KEY, conversation_id TEXT, mode TEXT, model TEXT, chat_window_index INTEGER, user_query TEXT, ai_response TEXT)''')
                # 建立PDF上傳記錄表格
                c.execute('''CREATE TABLE IF NOT EXISTS pdf_uploads
                             (id INTEGER PRIMARY KEY, pdf_path TEXT, embeddings_path TEXT, upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
            conn.close()
            print("資料庫初始化成功。")
        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
            raise

    def execute_query(self, query, params=()):
        # 執行資料庫查詢的輔助函數
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(query, params)
                conn.commit()
        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
            raise

    def fetch_query(self, query, params=()):
        # 提取資料庫查詢結果
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(query, params)
                results = c.fetchall()
            return results
        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
            raise

    def load_database(self):
        # 載入聊天記錄
        try:
            sql_query = "SELECT id, conversation_id, mode, model, chat_window_index, user_query, ai_response FROM chat_history"
            database = self.fetch_query(sql_query)
            if database:
                df_database = pd.DataFrame(database, columns=['id', 'conversation_id', 'mode', 'model', 'chat_window_index', 'user_query', 'ai_response'])
                return df_database
            else:
                return pd.DataFrame(columns=['id', 'conversation_id', 'mode', 'model', 'chat_window_index', 'user_query', 'ai_response'])
        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
            return pd.DataFrame(columns=['id', 'conversation_id', 'mode', 'model', 'chat_window_index', 'user_query', 'ai_response'])
        except Exception as e:
            # 處理其他錯誤
            print(f"發生錯誤: {e}")
            return pd.DataFrame(columns=['id', 'conversation_id', 'mode', 'model', 'chat_window_index', 'user_query', 'ai_response'])