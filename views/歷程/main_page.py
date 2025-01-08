import streamlit as st
from controllers.ui_controller import UIController
from models.batabase_userRecords import UserRecordsDB
# from views.login_page import LoginPage

class Sidebar:
    # ---物件: 側邊欄---
    def __init__(self, controller):
        """初始化側邊欄物件"""
        self.controller = controller
        self.userRecords_db = UserRecordsDB()
        # self.authenticator = LoginPage()

    def display(self):
        """顯示側邊欄"""
        self._set_sidebar_button_style()
        self._display_new_chat_button()
        self._display_agent_selection()
        self._display_llm_selection()
        self._display_chat_history_buttons()

    def _set_sidebar_button_style(self):
        """設定側邊欄按鈕的樣式"""
        st.markdown(f"""
            <style>
                div.stButton > button {{
                    background-color: transparent;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: -5px 0;
                    padding: 10px 20px;
                    width: 100%;
                    display: flex;                    
                    font-size: 30px !important;  /* 增大字體大小並提高優先級 */
                    justify-content: center; /* 水平居中 */
                    align-items: center; /* 垂直居中 */
                    text-align: center; /* 文字置中 */
                    white-space: nowrap; /* 禁止文本换行 */
                    overflow: hidden; /* 隐藏超出部分 */
                    text-overflow: ellipsis; /* 超出部分显示省略号 */
                }}
                div.stButton > button:hover {{
                    background-color: #e0e0e0;
                }}
            </style>
        """, unsafe_allow_html=True)

    def _display_agent_selection(self):
        """顯示助理類型選擇與資料庫選擇"""
        with st.sidebar:
            st.title("Agent")

            # 設定初始選項
            current_agent = st.session_state.get('agent', '一般助理')
            agent_options = ['一般助理', '個人KM', '資料庫查找助理', '資料庫查找助理2.0', 'SQL生成助理']
            selected_agent_index = agent_options.index(current_agent)

            # 顯示助理種類型選項，並設置默認選項為 current_agent
            selected_agent = st.radio(
                "請選擇助理種類型:",
                agent_options,
                index=selected_agent_index
            )

            # 如果更新 agent 選擇，則開啟新的聊天視窗並刷新頁面
            if selected_agent != st.session_state.get('agent'):
                st.session_state['agent'] = selected_agent
                self.controller.new_chat()

            # 如果所選助理需要資料庫選項，顯示資料庫選擇
            if selected_agent not in ['一般助理', '個人KM']:
                self._display_database_selection()

    def _display_database_selection(self):
        """根據選擇的助理類型顯示資料庫選項"""
        options = ["Oracle", "MSSQL", "SQLITE"]
        db_source = st.sidebar.selectbox('選擇資料來源:', options)
        # 儲存 db_name
        st.session_state['db_source'] = db_source

        if db_source == "Oracle":
            """顯示 Oracle 資料庫選項"""
            options = ["v2nbfc00_xd_QMS"]
            db_name = st.sidebar.selectbox('選擇資料庫:', options)
        elif db_source == "MSSQL":
            """顯示 MSSQL 資料庫選項"""
            options = ["NPC_3040"]
            db_name = st.sidebar.selectbox('選擇資料庫:', options)
        elif db_source == "SQLITE":
            """顯示 SQLite 資料庫選項"""
            options = ["CC17", "netincome"]
            db_name = st.sidebar.selectbox('選擇資料庫:', options)
        else:
            db_name = 'na'
        # 儲存 db_name
        st.session_state['db_name'] = db_name

    def _display_new_chat_button(self):
        """顯示新聊天按鈕"""
        with st.sidebar:
            if st.button("New Chat"):
                self.controller.new_chat()

    def _display_llm_selection(self):
        """顯示 LLM 模式選項"""
        with st.sidebar:
            st.title("LLM 選項")
            new_mode = st.radio("LLM 類型：", ('內部LLM', '外部LLM'))
            st.session_state['mode'] = new_mode

            if new_mode == '內部LLM':
                options = [
                    "Llama-3-8b",
                    "taiwan-llama-3-8b",
                    "taiwan-llm-13b",
                    "gemma2-9b-chinese"
                ]
                st.session_state['option'] = st.selectbox('選擇一個選項：', options)
            else:
                st.session_state['api_base'] = st.text_input('API 地址：', type='password')
                st.session_state['api_key'] = st.text_input('API 密鑰：', type='password')

    def _display_chat_history_buttons(self):
        """顯示側邊欄中的聊天記錄"""
        with st.sidebar:
            st.title("聊天記錄")
            num_chat_windows = st.session_state.get('num_chat_windows', 1)

            # 顯示聊天記錄按鈕
            for index in range(num_chat_windows + 1):
                chat_title = self.controller.get_title(index)

                # 創建選擇和刪除按鈕的列
                chat_window, delete_button = st.columns([4, 1])

                # 顯示選擇按鈕並設置當前聊天索引
                if chat_window.button(chat_title, key=f'chat_window_select_{index}'):
                    st.session_state['active_window_index'] = index
                    self.userRecords_db.get_active_window_setup(index)

                    # 根據選擇的聊天視窗，更新 agent 並刷新頁面
                    current_agent = st.session_state.get('agent')
                    st.session_state['agent'] = current_agent
                    st.rerun()

                # 顯示刪除按鈕
                if delete_button.button("X", key=f'chat_delete_{index}'):
                    if index == 0 and num_chat_windows == 0:
                        break
                    self.controller.delete_chat_history_and_update_indexes(index)
                    self._update_active_window_index(index, num_chat_windows)
                    st.rerun()

    def _update_active_window_index(self, deleted_index, total_windows):
        """更新目前視窗，若刪除的是當前聊天記錄，則更新當前聊天索引"""
        ###
        active_window_index = st.session_state.get('active_window_index')

        if active_window_index > deleted_index:
            st.session_state['active_window_index'] -= 1
        elif active_window_index == deleted_index:
            st.session_state['active_window_index'] = total_windows - 1
        else:
            pass


class MainContent:
    # ---物件: 主畫面內容---
    def __init__(self, controller, userRecords_db):
        """初始化主內容物件"""
        self.controller = controller
        self.userRecords_db = userRecords_db

    def display(self):
        """顯示主內容"""
        self._configure_page()
        self._display_input_fields()
        self._display_sql_example()
        self._display_active_chat_history()

    def _configure_page(self):
        """配置主頁面標題"""
        st.title("南亞塑膠GenAI")

    def _display_input_fields(self):
        """顯示文件上傳欄位，僅當選擇 '個人KM' 時顯示"""
        if st.session_state.get('agent') == '個人KM':
            st.session_state['source_docs'] = st.file_uploader(label="上傳文檔", type="pdf", accept_multiple_files=True)
            st.button("提交文件", on_click=self.controller.process_uploaded_documents, key="submit", help="提交文件", type='secondary')

    def _display_sql_example(self):
        """根據資料庫來源顯示 prompt"""
        db_source = st.session_state.get('db_source')
        db_name = st.session_state.get('db_name')
        selected_agent = st.session_state.get('agent')

        if selected_agent not in ['一般助理', '個人KM']:
            if db_source == "Oracle":
                st.write('輸入範例1：v2nbfc00_xd_QMS table, 尋找EMPID=N000175896的TEL')
            elif db_source == "MSSQL" and db_name == "NPC_3040":
                st.write('輸入範例1：anomalyRecords on 2023-10-10 10:40:01.000')
            elif db_source == "SQLITE":
                if db_name == "CC17":
                    st.write('輸入範例1：CC17中ACCT=8003RZ的第一筆資料')
                else:
                    st.write('輸入範例1：SALARE=荷蘭的TARIFFAMT總和')

    def _display_active_chat_history(self):
        """顯示聊天記錄"""
        self.userRecords_db.get_chat_history()
        chat_records = st.session_state.get('chat_history', [])

        if chat_records:
            for result in chat_records:
                with st.chat_message("user"):
                    st.markdown(f"{result['user_query']}")
                with st.chat_message("ai"):
                    st.markdown(f"{result['ai_response']}")

    def display_active_messages(self):
        """顯示用戶與AI之間的消息"""
        for message in st.session_state.get('messages', []):
            st.chat_message('user').write(message[0])
            st.chat_message('ai').write(message[1])
class MainPage:
    def __init__(self):
        """初始化主頁面物件"""
        self.controller = UIController()
        self.userRecords_db = UserRecordsDB()
        self.sidebar = Sidebar(self.controller)
        self.main_content = MainContent(self.controller, self.userRecords_db)
        #self.authenticator = self.create_authenticator()

    def show(self):
        """顯示主頁面"""
        self.controller.initialize_session_state()
        self.sidebar.display()
        self.main_content.display()

        if query := st.chat_input():
            self.controller.handle_query(query)
        self.main_content.display_active_messages()

        #self.authenticator.logout('登出', 'sidebar')


def main():
    """主函數"""
    main_page = MainPage()
    main_page.show()

if __name__ == "__main__":
    main()
