from pathlib import Path
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

class BaseDB:
    def __init__(self, db_path: Path):
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
        """初始化資料庫，創建必要的表格。子類別需要實現這個方法。"""
        raise NotImplementedError("子類別需要實現這個方法。")

    def execute_query(self, query: str, params=()):
        """執行資料庫的寫入操作。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
        except sqlite3.OperationalError as e:
            logging.error(f"execute_query 資料庫操作錯誤: {e}")
            raise

    def fetch_query(self, query: str, params=()):
        """執行資料庫的查詢操作並返回結果。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except sqlite3.OperationalError as e:
            logging.error(f"fetch_query 資料庫操作錯誤: {e}")
            raise
