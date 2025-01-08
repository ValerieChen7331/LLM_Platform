import pandas as pd
import streamlit as st

from models.batabase_base import BaseDB
from apis.file_paths import FilePaths

class UserRecordsDB(BaseDB):
    def __init__(self):
        self.file_paths = FilePaths()
        username = st.session_state.get('username')
        db_path = self.file_paths.get_user_records_dir().joinpath(username+'.db')
        super().__init__(db_path)
        self.columns = [
            'id', 'agent', 'mode', 'model',
            'db_source', 'db_name',
            'conversation_id', 'active_window_index', 'num_chat_windows', 'title',
            'user_query', 'ai_response'
        ]

    def _init_db(self):
        """初始化資料庫，創建必要的表格。"""
        chat_history_query = '''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
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
        print("UserRecordsDB 資料庫初始化成功。")

    def load_database(self) -> pd.DataFrame:
        """載入聊天記錄，並以 DataFrame 格式返回。"""
        query = f"SELECT {', '.join(self.columns)} FROM chat_history"
        empty_df = pd.DataFrame(columns=self.columns)

        try:
            data = self.fetch_query(query)
            if not data:
                return empty_df
            return pd.DataFrame(data, columns=self.columns)
        except Exception as e:
            print(f"load_database 發生錯誤: {e}")
            return empty_df

    def get_chat_history(self):
        """從資料庫中獲取並加載當前的聊天記錄。"""
        try:
            active_window_index = st.session_state.get('active_window_index')
            query = """
                SELECT id, conversation_id, active_window_index, user_query, ai_response
                FROM chat_history 
                WHERE active_window_index = ? 
                ORDER BY id
            """
            columns = ['id', 'conversation_id', 'active_window_index', 'user_query', 'ai_response']

            chat_history_data = self.fetch_query(query, (active_window_index,))
            if chat_history_data:
                # 創建 DataFrame 並檢查資料
                df_check = pd.DataFrame(chat_history_data, columns=columns)
                #print(df_check)  # 可選，根據需要打印檢查資料

                # 選擇所需的列
                chat_history_df = df_check[['user_query', 'ai_response']]
                st.session_state['chat_history'] = chat_history_df.to_dict(orient='records')
            else:
                st.session_state['chat_history'] = []

        except Exception as e:
            print(f"get_chat_history 發生錯誤: {e}")
            st.session_state['chat_history'] = []

    def get_active_window_setup(self, index):
        """從資料庫中獲取並加載當前的聊天記錄。"""
        try:
            query = """
                SELECT id, conversation_id, active_window_index, 
                agent, mode, model,
                db_source, db_name
                FROM chat_history 
                WHERE active_window_index = ? 
                ORDER BY id
            """
            columns = ['id', 'conversation_id', 'active_window_index',
                       'agent', 'mode', 'model',
                       'db_source', 'db_name']

            active_window_setup = self.fetch_query(query, (index,))
            if active_window_setup:
                # 創建 DataFrame 並檢查資料
                df_check = pd.DataFrame(active_window_setup, columns=columns)
                #print(df_check)  # 可選，根據需要打印檢查資料

                # 選擇所需的列並更新 session state
                for column in ['agent', 'db_name', 'db_source']:
                    st.session_state[column] = df_check[column].iloc[-1]
            else:
                pass

        except Exception as e:
            print(f"get_active_window_setup 發生錯誤: {e}")


    def pass_save_to_database(self, query: str, response: str):
        """將查詢結果保存到資料庫中。"""
        session_data = st.session_state  # 將 st.session_state 存入局部變量

        data = {
            'agent': session_data.get('agent', ''),
            'mode': session_data.get('mode', ''),
            'model': session_data.get('model', ''),

            'db_source': session_data.get('db_source', ''),
            'db_name': session_data.get('db_name', ''),
            'conversation_id': session_data.get('conversation_id', ''),
            'active_window_index': session_data.get('active_window_index', 0),
            'num_chat_windows': session_data.get('num_chat_windows', 0),
            'title': session_data.get('title', ''),
            'user_query': query,
            'ai_response': response,
        }
        if data['agent'] == '資料庫查找助理':
            data['mode'] = '內部LLM'
            data['model'] = 'duckdb-nsql'
        elif data['agent'] == '資料庫查找助理2.0':
            data['mode'] = '內部LLM'
            data['model'] = 'duckdb-nsql (2.0)'
        elif data['agent'] == 'SQL生成助理':
            data['mode'] = '內部LLM'
            data['model'] = 'duckdb-nsql (SQL生成助理)'



        # 插入資料
        self.execute_query(
            """
            INSERT INTO chat_history 
            (agent, mode, model, db_source, db_name, 
             conversation_id, active_window_index, num_chat_windows, title,
             user_query, ai_response) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(data.values())
        )

    def save_to_database(self, query: str, response: str):
        """將查詢結果保存到資料庫中。"""

        # 初始化 data 字典，從 session_state 中獲取數據
        data = {key: st.session_state.get(key, default) for key, default in {
            'agent': '',
            'mode': '',
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
            '資料庫查找助理2.0': ('內部LLM', 'duckdb-nsql (2.0)'),
            'SQL生成助理': ('內部LLM', 'duckdb-nsql (SQL生成助理)')
        }

        if data['agent'] in agent_settings:
            data['mode'], data['model'] = agent_settings[data['agent']]

        # 插入資料
        self.execute_query(
            """
            INSERT INTO chat_history 
            (agent, mode, model, db_source, db_name, 
             conversation_id, active_window_index, num_chat_windows, title,
             user_query, ai_response) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(data.values())
        )

