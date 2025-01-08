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
                embedding TEXT
            )
        '''
        self.execute_query(pdf_uploads_query)

        file_names_query = '''
                            CREATE TABLE IF NOT EXISTS file_names (
                                id INTEGER PRIMARY KEY,
                                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- UserRecordsDB 沒有
                                username TEXT,                                    -- UserRecordsDB 沒有
                                conversation_id TEXT,
                                tmp_name TEXT,             
                                org_name TEXT
                            )
                        '''
        self.execute_query(file_names_query)

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
            'ai_response': response
        }.items()}

        # 根據 agent 設置對應的 mode 和 model
        agent_settings = {
            '資料庫查找助理': ('內部LLM', 'codeqwen, wangshenzhi/llama3.1_8b_chinese_chat'),
            '資料庫查找助理2.0': ('內部LLM', 'duckdb-nsql, wangshenzhi/llama3.1_8b_chinese_chat'),
            'SQL生成助理': ('內部LLM', 'duckdb-nsql')
        }

        if data['agent'] in agent_settings:
            data['mode'], data['model'] = agent_settings[data['agent']]

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
            'embedding': ''
        }.items()}

        try:
            # 插入資料
            self.execute_query(
                """
                INSERT INTO pdf_uploads 
                (upload_time, username, conversation_id, agent, embedding) 
                VALUES (?, ?, ?, ?, ?)
                """,
                tuple(data.values())
            )
            logging.info("查詢結果已成功保存到資料庫 DevOpsDB (pdf_uploads)。")
        except Exception as e:
            # 記錄錯誤訊息
            logging.error(f"保存到 DevOpsDB (pdf_uploads) 資料庫時發生錯誤: {e}")


    def save_to_file_names(self):
        """將查詢結果保存到資料庫中。"""
        upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = st.session_state.get('username', '')
        conversation_id = st.session_state.get('conversation_id', '')
        doc_names = st.session_state.get('doc_names', {})

        for tmp_name, org_name in doc_names.items():
            try:
                # 插入資料
                self.execute_query(
                    """
                    INSERT INTO file_names 
                    (upload_time, username, conversation_id, tmp_name, org_name) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (upload_time, username, conversation_id, tmp_name, org_name)
                )
                logging.info(f"file_names 已成功保存到 DevOpsDB: tmp_name={tmp_name}, org_names={org_name}")
            except Exception as e:
                # 記錄錯誤訊息
                logging.error(f"file_names 保存到 DevOpsDB 時發生錯誤: {e}")
