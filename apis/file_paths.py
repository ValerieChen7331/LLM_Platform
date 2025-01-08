from pathlib import Path
import streamlit as st

class FilePaths:
    def __init__(self, base_dir=None):
        # 設定 TMP_DIR、LOCAL_VECTOR_STORE_DIR 和 OUTPUT_DIR 的路徑
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.joinpath('data')
        else:
            base_dir = Path(base_dir)  # 確保 base_dir 是 Path 對象

        username = st.session_state.get('username')
        conversation_id = st.session_state.get('conversation_id')

        self.TMP_DIR = base_dir.joinpath(f"user/{username}/tmp")
        self.LOCAL_VECTOR_STORE_DIR = base_dir.joinpath(f"user/{username}/vector_store/{conversation_id}")
        self.OUTPUT_DIR = base_dir.joinpath('output')
        self.User_Records_DIR = base_dir.joinpath('user')
        self.DevOps_DIR = base_dir.joinpath('developer')

    def get_tmp_dir(self):
        # 獲取 TMP_DIR
        return self.TMP_DIR

    def get_local_vector_store_dir(self):
        # 獲取 LOCAL_VECTOR_STORE_DIR
        return self.LOCAL_VECTOR_STORE_DIR

    def get_output_dir(self):
        # 獲取 OUTPUT_DIR
        return self.OUTPUT_DIR

    def get_user_records_dir(self):
        # 獲取 User_Records_DIR
        return self.User_Records_DIR

    def get_devOps_dir(self):
        # 獲取 DevOps_DIR
        return self.DevOps_DIR
