import streamlit as st

class MainContent:
    def __init__(self, controller, userRecords_db):
        """初始化主內容物件"""
        self.controller = controller
        self.userRecords_db = userRecords_db

    def display(self):
        """顯示主內容"""
        self._configure_page()          # 頁面標題
        self._display_input_fields()    # 顯示文件上傳欄位
        self._display_sql_example()     # 資料庫範例
        self._display_active_chat_history()     # 顯示聊天記錄

    def _configure_page(self):
        """配置主頁面標題"""
        st.title("南亞塑膠生成式AI")
        st.write(f'*Welcome {st.session_state["name"]}*')

    def _display_input_fields(self):
        """顯示文件上傳欄位，僅當選擇 '個人KM' 時顯示"""
        # 只在 '個人KM' 時執行
        if st.session_state.get('agent') == '個人KM':
            # 顯示文件上傳欄位，允許上傳多個 PDF 文件
            st.session_state['source_docs'] = st.file_uploader(label="上傳文檔", type="pdf", accept_multiple_files=True)
            # 顯示提交按鈕，點擊時觸發 process_uploaded_documents 方法
            st.button("提交文件", on_click=self.controller.process_uploaded_documents, key="submit", help="提交文件")

    def _display_sql_example(self):
        """根據資料庫來源顯示 prompt"""
        db_source = st.session_state.get('db_source')
        db_name = st.session_state.get('db_name')
        selected_agent = st.session_state.get('agent')

        if selected_agent not in ['一般助理', '個人KM']:
            # 顯示 Oracle 資料庫的輸入範例
            if db_source == "Oracle":
                st.write('輸入範例1：v2nbfc00_xd_QMS table, 尋找EMPID=N000175896的TEL')

            # 顯示 MSSQL 資料庫的輸入範例
            elif db_source == "MSSQL" and db_name == "NPC_3040":
                st.write('輸入範例1：anomalyRecords on 2023-10-10 10:40:01.000')

            # 顯示 SQLITE 資料庫的輸入範例（CC17 資料庫）
            elif db_source == "SQLITE":
                if db_name == "CC17":
                    st.write('輸入範例1：CC17中ACCT=8003RZ的第一筆資料')
                else:
                    # 顯示 SQLITE 資料庫的輸入範例（netincome 資料庫）
                    st.write('輸入範例1：SALARE=荷蘭的TARIFFAMT總和')

    def _display_active_chat_history(self):
        """顯示聊天記錄"""
        # 從user資料庫中取得聊天記錄
        # self.userRecords_db.get_chat_history()
        chat_records = st.session_state.get('chat_history', [])
        if chat_records:
            # 迭代顯示每一條聊天記錄
            for result in chat_records:
                with st.chat_message("user"):
                    st.markdown(result['user_query'])
                with st.chat_message("ai"):
                    st.markdown(result['ai_response'])

