import streamlit as st
from models.batabase_userRecords import UserRecordsDB
class Sidebar:
    def __init__(self, controller):
        """初始化側邊欄物件"""
        self.controller = controller
        self.userRecords_db = UserRecordsDB()   # 初始化用戶記錄資料庫物件

    def display(self):
        """顯示側邊欄"""
        self._set_sidebar_button_style()      # 設定側邊欄按鈕樣式
        self._display_new_chat_button()       # 顯示新聊天按鈕
        self._display_agent_selection()       # 顯示助理類型選擇
        self._display_llm_selection()         # 顯示 LLM 模式選項
        self._display_chat_history_buttons()  # 顯示聊天記錄按鈕

    def _set_sidebar_button_style(self):
        """設定側邊欄按鈕的樣式"""
        st.markdown("""
            <style>
                div.stButton > button {
                    background-color: transparent;  /* 設定按鈕背景為透明 */
                    border: 1px solid #ccc;         /* 設定按鈕邊框顏色 */
                    border-radius: 5px;             /* 設定按鈕邊框圓角 */
                    font-weight: bold;              /* 設定按鈕字體加粗 */
                    margin: -5px 0;                 /* 設定按鈕上下邊距 */
                    padding: 10px 20px;             /* 設定按鈕內距 */
                    width: 100%;                    /* 設定按鈕寬度為 100% */
                    display: flex;                  /* 使用 flex 布局 */
                    font-size: 30px !important;     /* 設定按鈕字體大小 */
                    justify-content: center;        /* 設定按鈕內容水平居中 */
                    align-items: center;            /* 設定按鈕內容垂直居中 */
                    text-align: center;             /* 設定按鈕文字居中對齊 */
                    white-space: nowrap;            /* 設定文字不換行 */
                    overflow: hidden;               /* 隱藏超出範圍的內容 */
                    text-overflow: ellipsis;        /* 使用省略號表示超出範圍的文字 */
                    line-height: 1.2;               /* 設定行高，讓文字保持在一行內 */
                    height: 1.2em;                  /* 設定按鈕高度僅能容納一行文字 */
                }
                div.stButton > button:hover {
                    background-color: #e0e0e0;  /* 設定按鈕懸停時的背景顏色 */
                }
            </style>
        """, unsafe_allow_html=True)  # 使用 HTML 和 CSS 設定按鈕樣式

    def _display_agent_selection(self):
        """顯示助理類型選擇與資料庫選擇"""
        with st.sidebar:
            st.title("Agent")

            current_agent = st.session_state.get('agent', '一般助理')   # 取得當前的助理類型
            agent_options = ['一般助理', '個人KM', '資料庫查找助理', '資料庫查找助理2.0', 'SQL生成助理']
            selected_agent_index = agent_options.index(current_agent)   # 取得當前助理類型在選項中的索引位置

            selected_agent = st.radio(
                "請選擇助理種類型:",
                agent_options,      # 助理類型選項列表
                index=selected_agent_index  # 預設選擇當前助理類型
            )

            # 如果選擇的助理類型改變
            if selected_agent != st.session_state.get('agent'):
                st.session_state['agent'] = selected_agent
                # 開啟新的聊天窗口
                self.controller.new_chat()

            # 顯示資料庫選項
            if selected_agent not in ['一般助理', '個人KM']:
                self._display_database_selection()

    def _display_database_selection(self):
        """根據選擇的助理類型顯示資料庫選項"""
        options = ["Oracle", "MSSQL", "SQLITE"]

        # 使用已保存的值作為預設值（如果存在且有效）
        try:
            db_source_index = options.index(st.session_state.get('db_source', options[0]))
        except ValueError:
            db_source_index = 0  # 如果不存在於列表中，使用第一個作為預設值

        db_source = st.sidebar.selectbox('選擇資料來源:', options, index=db_source_index)
        st.session_state['db_source'] = db_source

        # 根據選擇的資料來源設定資料庫選項
        if db_source == "Oracle":
            db_options = ["v2nbfc00_xd_QMS"]
        elif db_source == "MSSQL":
            db_options = ["NPC_3040"]
        elif db_source == "SQLITE":
            db_options = ["CC17", "netincome"]
        else:
            db_options = ['na']

        # 使用已保存的值作為預設值（如果存在且有效）
        try:
            db_name_index = db_options.index(st.session_state.get('db_name', db_options[0]))
        except ValueError:
            db_name_index = 0  # 如果不存在於列表中，使用第一個作為預設值

        db_name = st.sidebar.selectbox('選擇資料庫:', db_options, index=db_name_index)
        st.session_state['db_name'] = db_name

    def _display_new_chat_button(self):
        """顯示新聊天按鈕"""
        with st.sidebar:
            if st.button("New Chat"):
                # 點擊按鈕後，啟動新的聊天
                self.controller.new_chat()

    def _display_llm_selection(self):
        """顯示 LLM 模式選項"""
        with st.sidebar:
            st.title("LLM 選項")
            new_mode = st.radio("LLM 類型：", ('內部LLM', '外部LLM'))
            st.session_state['mode'] = new_mode

            if new_mode == '內部LLM':
                options = ["Llama-3-8b", "taiwan-llama-3-8b", "taiwan-llm-13b", "gemma2-9b-chinese"]
                st.session_state['option'] = st.selectbox('選擇一個選項：', options)
            else:
                st.session_state['api_base'] = st.text_input('API 地址：', type='password')
                st.session_state['api_key'] = st.text_input('API 密鑰：', type='password')

    def _display_chat_history_buttons(self):
        """顯示側邊欄中的聊天記錄"""
        with st.sidebar:
            st.title("聊天記錄")
            # 取得目前的聊天窗口數量
            num_chat_windows = st.session_state.get('num_chat_windows')

            for index in range(num_chat_windows):
                chat_title = self.controller.get_title(index)   # 取得聊天窗口的標題
                chat_window, delete_button = st.columns([4, 1]) # 設置標題和刪除按鈕

                # 點擊 window, 回到過去聊天紀錄的設定
                if chat_window.button(chat_title, key=f'chat_window_select_{index}'):
                    st.session_state['active_window_index'] = index
                    self.userRecords_db.get_active_window_setup(index)  # 取得聊天窗口設定
                    st.rerun()  # 重新執行應用程式

                if delete_button.button("X", key=f'chat_delete_{index}'):
                    if index == 0 and num_chat_windows == 0:
                        break
                    else:
                        self.controller.delete_chat_history_and_update_indexes(index)   # 刪除聊天記錄並更新索引
                        self._update_active_window_index(index, num_chat_windows)   # 更新目前活動的窗口索引
                    st.rerun()

    def _update_active_window_index(self, deleted_index, total_windows):
        """更新目前視窗索引"""
        active_window_index = st.session_state.get('active_window_index')

        if active_window_index > deleted_index:
            st.session_state['active_window_index'] -= 1

        # 如果刪除的窗口就是當前活動窗口，則將索引設為最後一個窗口
        elif active_window_index == deleted_index:
            st.session_state['active_window_index'] = total_windows - 1
