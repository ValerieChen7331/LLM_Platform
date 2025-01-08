import pandas as pd
import streamlit as st
import uuid
import shutil
import logging

from models.batabase_base import BaseDB
from apis.file_paths import FilePaths

logging.basicConfig(level=logging.INFO)
class UserRecordsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        username = st.session_state.get('username')
        db_path = self.file_paths.get_user_records_dir().joinpath(username+'.db')
        super().__init__(db_path)

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        chat_history_query = '''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
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

        pdf_uploads_query = '''
            CREATE TABLE IF NOT EXISTS pdf_uploads (
                id INTEGER PRIMARY KEY,
                conversation_id TEXT,
                agent TEXT,             
                embedding TEXT,
                doc_names TEXT
            )
        '''
        self.execute_query(pdf_uploads_query)
        logging.info("UserRecordsDB 資料庫初始化成功。")

    def load_database(self, database) -> pd.DataFrame:
        """載入聊天記錄，並以 DataFrame 格式返回。"""
        all_columns = [
            'id', 'agent', 'mode', 'llm_option', 'model',
            'db_source', 'db_name',
            'conversation_id', 'active_window_index', 'num_chat_windows', 'title',
            'user_query', 'ai_response'
        ]
        query = f"SELECT {', '.join(all_columns)} FROM {database}"
        empty_df = pd.DataFrame(columns=all_columns)

        try:
            data = self.fetch_query(query)
            if not data:
                return empty_df
            return pd.DataFrame(data, columns=all_columns)
        except Exception as e:
            st.error(f"load_database 發生錯誤: {e}")
            return empty_df

    def get_active_window_setup(self, index):
        """從資料庫中獲取並加載當前的聊天記錄。"""
        try:
            # 定義所需的列
            setup_columns = ['conversation_id', 'agent', 'mode', 'llm_option', 'model', 'db_source', 'db_name', 'title']
            history_columns = ['user_query', 'ai_response']

            # 合併所有列
            all_columns = setup_columns + history_columns

            # SQL 查詢，用於獲取指定 active_window_index 的聊天記錄
            query = """
                SELECT conversation_id, agent, mode, llm_option, model, db_source, db_name, title,
                       user_query, ai_response
                FROM chat_history 
                WHERE active_window_index = ? 
                ORDER BY id
            """

            # 執行查詢並獲取結果
            active_window_setup = self.fetch_query(query, (index,))

            # 檢查是否有結果返回
            if active_window_setup:
                # 創建 DataFrame 並檢查資料
                df_check = pd.DataFrame(active_window_setup, columns=all_columns)

                # 更新 session state 的設置列
                for column in setup_columns:
                    st.session_state[column] = df_check[column].iloc[-1]

                # 更新 chat_history 並轉換為字典格式
                chat_history_df = df_check[history_columns]
                st.session_state['chat_history'] = chat_history_df.to_dict(orient='records')
            else:
                # 如果無結果，重置 session state 為預設值
                self.reset_session_state_to_defaults()

        except Exception as e:
            st.error(f"get_active_window_setup 發生錯誤: {e}")

    def reset_session_state_to_defaults(self):
        """重置 session state 參數至預設值。"""
        reset_session_state = {
            #'agent': '一般助理',
            'mode': '內部LLM',
            'llm_option': 'Qwen2-Alibaba',
            'model': '',
            'api_base': None,
            'api_key': None,
            'db_name': None,
            'db_source': None,
            'title': '',
            'chat_history': []
        }
        for key, value in reset_session_state.items():
            st.session_state[key] = value

    def save_to_database(self, query: str, response: str):
        """將查詢結果保存到資料庫中。"""

        # 初始化 data 字典，從 session_state 中獲取數據
        data = {key: st.session_state.get(key, default) for key, default in {
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

        # 根據 agent 設置對應的 mode 和 model
        agent_settings = {
            '資料庫查找助理': ('內部LLM', 'duckdb-nsql'),
            '資料庫查找助理2.0': ('內部LLM', 'duckdb-nsql'),
            'SQL生成助理': ('內部LLM', 'duckdb-nsql')
        }

        if data['agent'] in agent_settings:
            data['mode'], data['model'] = agent_settings[data['agent']]

        try:
            # 插入資料
            self.execute_query(
                """
                INSERT INTO chat_history 
                (agent, mode, llm_option, model, db_source, db_name, 
                 conversation_id, active_window_index, num_chat_windows, title,
                 user_query, ai_response) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            logging.info("查詢結果已成功保存到資料庫 UserDB (chat_history)")

        except Exception as e:
            logging.error(f"保存到 UserDB (chat_history) 資料庫時發生錯誤: {e}")

    def save_to_pdf_uploads(self):
        """將查詢結果保存到資料庫中。"""

        # 初始化 data 字典，從 session_state 中獲取數據
        data = {key: st.session_state.get(key, default) for key, default in {
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
                (conversation_id, agent, embedding, doc_names ) 
                VALUES (?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            logging.info("查詢結果已成功保存到資料庫 UserDB (pdf_uploads)")
        except Exception as e:
            # 記錄錯誤訊息
            logging.error(f"保存到 UserDB (pdf_uploads) 資料庫時發生錯誤: {e}")

    def delete_vector_db(self, index, conversation_id):
        # 刪除資料夾
        st.session_state['conversation_id'] = conversation_id
        directory_path = self.file_paths.get_local_vector_store_dir()
        try:
            logging.info(f"Deleting vector db: {directory_path}")
            shutil.rmtree(directory_path)
        except Exception as e:
            logging.error(f"Error deleting vector db {directory_path}: {e}")

    def get_conversation_id(self, index):
        """從資料庫中獲取指定 active_window_index 的 conversation_id。"""
        try:
            query = """
                SELECT conversation_id FROM chat_history 
                WHERE active_window_index = ? 
            """
            # 假設 fetch_query 返回的是一個 list of tuples，例如：[(1,), (2,)]
            result = self.fetch_query(query, (index,))

            if result:
                # 直接提取最後一個 conversation_id
                return result[-1][0]
            else:
                return None  # 如果沒有找到資料，則設為 None

        except Exception as e:
            st.error(f"get_conversation_id 發生錯誤: {e}")


    def get_agent(self, index):
        """從資料庫中獲取指定 active_window_index 的 agent"""
        try:
            query = """
                SELECT agent FROM chat_history 
                WHERE active_window_index = ? 
            """
            #
            result = self.fetch_query(query, (index,))

            if result:
                # 直接提取最後一個 conversation_id
                return result[-1][0]
            else:
                return '一般助理'

        except Exception as e:
            st.error(f"get_agent 發生錯誤: {e}")