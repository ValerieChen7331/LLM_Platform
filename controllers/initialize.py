import uuid
import pandas as pd
from models.database_userRecords import UserRecordsDB
from apis.file_paths import FilePaths


class SessionInitializer:
    def __init__(self, username, base_dir=None):
        """
        初始化 SessionInitializer，設置使用者名稱和文件路徑。

        參數:
            username (str): 使用者名稱。
            base_dir (str, optional): 基本目錄路徑，默認為 None。
        """
        self.username = username
        self.file_paths = FilePaths(base_dir)

    def initialize_session_state(self):
        """初始化 Session 狀態，並儲存到字典 chat_session_data 中。"""
        # 從 user_records_db 載入資料，只取 active_window_index 欄位
        userRecords_db = UserRecordsDB(self.username)
        database = userRecords_db.load_database(
            'chat_history',
            ['active_window_index'])

        # 設置聊天窗口的數量及活躍窗口索引
        if not database.empty:
            num_chat_windows = len(set(database['active_window_index']))
        else:
            num_chat_windows = 0

        active_window_index = num_chat_windows
        num_chat_windows += 1  # 為新聊天窗口增加計數

        # 初始化 session 狀態參數，並儲存到 chat_session_data 字典中
        chat_session_data = {
            'conversation_id': str(uuid.uuid4()),  # 新的對話 ID
            'num_chat_windows': num_chat_windows,
            'active_window_index': active_window_index,
            'agent': '一般助理',
            'mode': '內部LLM',
            'llm_option': 'Gemma2',
            'model': 'gemma2:latest',
            'api_base': '',
            'api_key': '',
            'embedding': 'bge-m3',
            'doc_names': '',
            'db_name': '',
            'db_source': '',
            'chat_history': [],
            'title': '',

            'upload_time': None,
            'username': self.username,  # 設置使用者名稱

            'empty_window_exists': True  # 確保新窗口存在
        }
        return chat_session_data

    # def _initialize_load_database(self, database, columns=None) -> pd.DataFrame:
    #     """載入聊天記錄，並以 DataFrame 格式返回。
    #
    #     參數:
    #         database (str): 資料庫名稱。
    #         columns (list, optional): 欲選取的欄位名稱列表。若未提供，則使用預設的所有欄位。
    #
    #     返回:
    #         pd.DataFrame: 聊天記錄的 DataFrame。
    #     """
    #     # 獲取使用者紀錄的資料庫路徑
    #     db_path = self.file_paths.get_user_records_dir(self.username).joinpath(f"{self.username}.db")
    #     base_db = BaseDB(db_path)
    #
    #     # 預設的所有欄位
    #     all_columns = [
    #         'id', 'agent', 'mode', 'llm_option', 'model',
    #         'db_source', 'db_name', 'conversation_id', 'active_window_index',
    #         'num_chat_windows', 'title', 'user_query', 'ai_response'
    #     ]
    #
    #     # 使用指定的欄位或預設欄位
    #     selected_columns = columns if columns else all_columns
    #     # SQL 查詢語句
    #     query = f"SELECT {', '.join(selected_columns)} FROM {database}"
    #
    #     # 預設為空的 DataFrame，作為返回值
    #     empty_df = pd.DataFrame(columns=selected_columns)
    #
    #     try:
    #         # 執行查詢以獲取數據
    #         data = base_db.fetch_query(query)
    #         if not data:
    #             return empty_df
    #
    #         # 返回包含數據的 DataFrame
    #         return pd.DataFrame(data, columns=selected_columns)
    #     except Exception as e:
    #         # 紀錄錯誤並返回空的 DataFrame
    #         print(f"_initialize_load_database: {e}")
    #         return empty_df
