from services.llm_services import LLMService
from services.document_services import DocumentService
from models.database_userRecords import UserRecordsDB
import streamlit as st
import uuid
import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os
class UIController:
    def __init__(self):
        # 初始化 LLMService 和 DocumentService
        self.llm_service = LLMService()
        self.doc_service = DocumentService()
        self.userRecords_db = UserRecordsDB()

    def initialize_session_state(self):
        # 從 userRecords_db 載入資料
        database = self.userRecords_db.load_database('chat_history')

        # 設置聊天窗口的數量及活躍窗口索引
        if not database.empty:
            count_chat_windows = len(set(database['active_window_index']))
            active_window_index = count_chat_windows    # 開機預設: 新的 window
            count_chat_windows += 1                     # 總共 n+1 個 windows
        else:
            count_chat_windows = 1      # 總共 1 個 window
            active_window_index = 0     # 開機預設: 1 個新的 window

        # 初始化 session 狀態參數
        default_session_params = {
            'conversation_id': str(uuid.uuid4()),
            'num_chat_windows': count_chat_windows,
            'active_window_index': active_window_index,

            'agent': '一般助理',
            'mode': '內部LLM',
            'llm_option': 'Qwen2-Alibaba',
            'model': '',
            'api_base': None,
            'api_key': None,

            'embedding': None,
            'doc_names': '',
            'db_name': None,
            'db_source': None,

            #'messages': [],
            'chat_history': [],
            'title': '',

            'empty_window_exists': True
        }

        for key, value in default_session_params.items():
            st.session_state.setdefault(key, value)

        print('----------------')
        print('num_chat_windows')
        print(st.session_state['num_chat_windows'])
        print('active_window_index')
        print(st.session_state['active_window_index'])
        print('----------------')

    def get_title(self, index):
        # 從資料庫加載數據
        df_database = self.userRecords_db.load_database('chat_history')

        # 過濾出匹配 active_window_index 的行
        df_window = df_database[df_database['active_window_index'] == index]

        # 如果找到匹配的行，將標題設置到 session state 中
        if not df_window.empty:
            title = df_window['title'].iloc[0]
        else:
            # 若未找到匹配的行，設置默認標題
            title = "(新對話)"
        return title

    def new_chat(self):
        # 創建新聊天窗口，更新 session 狀態
        if st.session_state.get('empty_window_exists'):
            st.session_state['active_window_index'] = st.session_state.get('num_chat_windows') - 1
        else:
            st.session_state['active_window_index'] = st.session_state.get('num_chat_windows')
            st.session_state['num_chat_windows'] += 1

        st.session_state['conversation_id'] = str(uuid.uuid4())
        self.userRecords_db.reset_session_state_to_defaults()
        st.session_state['empty_window_exists'] = True


    def delete_chat_history_and_update_indexes(self, delete_index):
        # 刪除指定聊天窗口索引的聊天歷史記錄
        self.userRecords_db.execute_query(  # 使用 userRecords_db 而非 database_model
            "DELETE FROM chat_history WHERE active_window_index = ?", (delete_index,))

        # 更新剩餘聊天窗口的索引
        chat_histories = self.userRecords_db.fetch_query(  # 使用 userRecords_db 而非 database_model
            "SELECT id, active_window_index FROM chat_history ORDER BY active_window_index")

        for id, active_window_index in chat_histories:
            if active_window_index > delete_index:
                new_index = active_window_index - 1
                self.userRecords_db.execute_query(  # 使用 userRecords_db 而非 database_model
                    "UPDATE chat_history SET active_window_index = ? WHERE id = ?", (new_index, id))

        # 更新 session state 中的聊天窗口索引
        st.session_state['num_chat_windows'] -= 1

    def save_response_to_pdf_with_chinese(self, response_content, file_name):
        # 初始化 Canvas 來創建 PDF
        c = canvas.Canvas(file_name, pagesize=letter)
        width, height = letter

        # 設置中文字體，這裡使用 .ttf 格式的 NotoSansCJK 字體
        font_path = "NotoSansCJKsc-Regular.ttf"  # 確保這個路徑指向你的 .ttf 文件
        if not os.path.exists(font_path):
            st.error("找不到 NotoSansCJK 字體文件，請確保該字體已安裝")
            return

        pdfmetrics.registerFont(TTFont('NotoSansCJK', font_path))
        c.setFont("NotoSansCJK", 12)

        # 將回應內容寫入 PDF，每行 80 個字符
        lines = response_content.split('\n')
        y_position = height - 40  # 初始行的位置

        for line in lines:
            wrapped_lines = self.wrap_text(line, 80)  # 將文本分行處理
            for wrapped_line in wrapped_lines:
                c.drawString(40, y_position, wrapped_line)
                y_position -= 14  # 每行往下移動
                if y_position < 40:  # 防止超出頁面範圍
                    c.showPage()
                    y_position = height - 40

        # 保存 PDF
        c.save()

        return file_name

    def wrap_text(self, text, max_length):
        """將長文本分行"""
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    def handle_query(self, query):
        # 處理使用者查詢，發送給 LLM 並顯示回應
        st.chat_message("human").write(query)
        response = self.llm_service.query(query)
        st.chat_message("ai").write(response)

        """# 使用 reportlab 生成包含中文的 PDF 並提供下載
        file_name = f"response_{str(uuid.uuid4())}.pdf"
        file_path = self.save_response_to_pdf_with_chinese(response, file_name)

        with open(file_path, "rb") as f:
            st.download_button(
                label="下載回應內容為 PDF",
                data=f,
                file_name=file_name,
                mime="application/pdf"
            )"""

    def process_uploaded_documents(self):
        # 處理上傳的文件
        self.doc_service.process_uploaded_documents()

