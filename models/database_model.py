from pathlib import Path
import sqlite3
import pandas as pd


class DatabaseModel:
    def __init__(self):
        # 初始化資料庫路徑並建立資料庫
        self.db_path = Path(__file__).resolve().parent.parent.joinpath('data', 'chat_history.db')
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

