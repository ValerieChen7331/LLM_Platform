import streamlit as st
from services.document_services import DocumentService

class MainContent:
    def __init__(self, chat_session_data):
        """初始化主內容物件"""
        self.chat_session_data = chat_session_data

    def display(self):
        """顯示主內容"""
        # 配置頁面標題
        self.configure_page()
        # 顯示文件上傳欄位
        if self.chat_session_data.get('agent') == '個人KM':
            self.display_input_fields()
        # 顯示資料庫範例
        # if self.chat_session_data.get('agent') not in ['一般助理', '個人KM']:
        #     self.display_sql_example()
        # 顯示聊天記錄
        self.display_active_chat_history()

    def configure_page(self):
        """配置主頁面標題"""
        st.title("南亞塑膠生成式AI")
        st.write(f'*Welcome {st.session_state["name"]}*')  # 顯示歡迎訊息

    def display_input_fields(self):
        """顯示文件上傳欄位，僅當選擇 '個人KM' 時顯示"""
        if self.chat_session_data.get('agent') == '個人KM':
            # 顯示文件上傳欄位，允許上傳多個 PDF 文件
            uploaded_files = st.file_uploader(label="上傳文檔", type="pdf", accept_multiple_files=True)
            # 準備文件列表，包含文件名和內容
            source_docs = [{'name': file.name, 'content': file.read()} for file in uploaded_files] if uploaded_files else []

            # 顯示提交按鈕，點擊時觸發 process_uploaded_documents 方法
            if st.button("提交文件", key="submit", help="提交文件"):
                try:
                    self.chat_session_data = DocumentService(self.chat_session_data).process_uploaded_documents(source_docs)
                except Exception as e:
                    st.error(f"處理文檔時發生錯誤：{e}")

            st.write(f'此功能仍在測試階段...')  # 顯示測試階段提示

    def display_sql_example(self):
        """根據資料庫來源顯示 prompt"""
        db_source = self.chat_session_data.get('db_source')
        db_name = self.chat_session_data.get('db_name')
        selected_agent = self.chat_session_data.get('agent')

        if selected_agent not in ['一般助理', '個人KM']:
            # 顯示 Oracle 資料庫的輸入範例
            if db_source == "Oracle":
                st.write('輸入範例1：v2nbfc00_xd_QMS table, 尋找EMPID=N000175896的TEL')

            # 顯示 MSSQL 資料庫的輸入範例
            elif db_source == "MSSQL" and db_name == "NPC_3040":
                st.write('輸入範例1：anomalyRecords on 2023-10-10 10:40:01.000')

            # 顯示 SQLITE 資料庫的輸入範例
            elif db_source == "SQLITE":
                if db_name == "CC17":
                    st.write('輸入範例1：CC17中ACCT=8003RZ的第一筆資料')
                else:
                    st.write('輸入範例1：SALARE=荷蘭的TARIFFAMT總和')

    def display_active_chat_history(self):
        """顯示聊天記錄"""
        chat_records = self.chat_session_data.get('chat_history', [])
        if chat_records:
            # 迭代顯示每一條聊天記錄
            for result in chat_records:
                with st.chat_message("user"):
                    st.markdown(result['user_query'])
                with st.chat_message("ai"):
                    st.markdown(result['ai_response'])

