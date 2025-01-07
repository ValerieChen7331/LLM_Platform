import streamlit as st
from controllers.ui_controller import UIController
from services.llm_services import LLMService
from models.database_model import UserRecordsDB

class MainPage:
    def __init__(self):
        self.controller = UIController()
        self.llm_service = LLMService()
        self.user_records_db = UserRecordsDB()

    def configure_page(self):
        # 設定頁面標題
        st.title("南亞塑膠GenAI")

    def new_chat_button_style(self):
        # New Chat 按鈕樣式
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
                }}
                div.stButton > button:hover {{
                    background-color: #e0e0e0;
                }}
            </style>
            """, unsafe_allow_html=True)

    def input_fields(self):
        # 上傳文件欄位
        st.session_state['source_docs'] = st.file_uploader(label="上傳文檔", type="pdf", accept_multiple_files=True)

    def display_submit_button(self):
        # 顯示 提交文件 按鈕
        st.button("提交文件", on_click=self.controller.process_uploaded_documents, key="submit", help="提交文件",
                  type='secondary')

    def display_sidebar(self):
        # 側邊欄選項
        self._sidebar_new_chat()
        self._sidebar_llm_mode()
        self._sidebar_chat_history()

    def _sidebar_new_chat(self):
        # 顯示新聊天按鈕
        with st.sidebar:
            if st.button("New Chat"):
                self.controller.new_chat()
                st.rerun()  # 刷新頁面

    def _sidebar_llm_mode(self):
        # 顯示 LLM 模式選項
        with st.sidebar:
            st.title("選項")
            new_mode = st.radio("LLM 類型：", ('內部LLM', '外部LLM'))
            st.session_state['mode'] = new_mode

            if st.session_state['mode'] == '內部LLM':
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

    def _sidebar_chat_history(self):
        # 顯示聊天記錄
        with st.sidebar:
            st.title("聊天記錄")
            if st.session_state['chat_window_index'] > 0:
                self._chat_history_buttons()

    def _chat_history_buttons(self):
        # 聊天記錄按鈕
        count_chat_windows = st.session_state['chat_window_index'] + 1

        for current_index in range(count_chat_windows):
            # 獲取聊天標題
            chat_title = self.controller.get_title(current_index)

            # 創建選擇和刪除按鈕的列
            chat_window, delete_button = st.columns([4, 1])

            # 顯示選擇按鈕並設置當前聊天索引
            if chat_window.button(chat_title, key=f'chat_window_select_{current_index}'):
                st.session_state['current_chat_window_index'] = current_index

            # 顯示刪除按鈕
            if delete_button.button("X", key=f'chat_delete_{current_index}'):
                # 刪除指定的聊天記錄並更新索引
                self.controller.delete_chat_history_and_update_indexes(current_index)

                # 若刪除的是當前聊天記錄，則更新當前聊天索引
                if st.session_state['current_chat_window_index'] >= count_chat_windows - 1:
                    st.session_state['current_chat_window_index'] = max(0, current_index - 1)

                # 刷新頁面以更新顯示
                st.rerun()

    def display_chat_history(self):
        """顯示聊天記錄"""
        self.user_records_db.get_chat_history()
        # 取得聊天記錄
        chat_records = st.session_state.get('chat_history', [])

        if chat_records:
            # 迭代每一條聊天記錄並顯示
            for result in chat_records:
                with st.chat_message("user"):
                    st.markdown(f"{result['user_query']}")
                with st.chat_message("ai"):
                    st.markdown(f"{result['ai_response']}")
        else:
            pass

    def display_messages(self):
        # 顯示消息
        for message in st.session_state.get('messages', []):
            st.chat_message('user').write(message[0])
            st.chat_message('ai').write(message[1])

    def logout(self):
        st.session_state['logged_in'] = False
        st.experimental_set_query_params(page="login")
        st.experimental_rerun()

    def show_main_page(self):
        # 顯示主頁面
        self.configure_page()
        self.new_chat_button_style()
        self.controller.initialize_session_state()
        self.input_fields()
        self.display_submit_button()
        self.display_sidebar()
        self.display_chat_history()

        if query := st.chat_input():
            self.controller.handle_query(query)
        self.display_messages()

        st.sidebar.button("Logout", on_click=self.logout)

def main():
    # 主函數
    main_page = MainPage()
    main_page.show_main_page()


if __name__ == "__main__":
    main()
