import streamlit as st
from models.database_userRecords import UserRecordsDB
from models.document_model import DocumentModel
from controllers.ui_controller import UIController

class Sidebar:
    def __init__(self):
        """初始化側邊欄物件"""
        self.controller = UIController()
        self.userRecords_db = UserRecordsDB()
        self.document_model = DocumentModel()

        # 助理類型選項
        self.agent_options = ['一般助理', '個人KM', '資料庫查找助理', '資料庫查找助理2.0', 'SQL生成助理']
        # 資料來源選項
        self.db_source_options = ["Oracle", "MSSQL", "SQLITE"]
        # 根據資料來源選擇對應的資料庫選項
        self.db_name = {
            "Oracle": ["v2nbfc00_xd_QMS"],
            "MSSQL": ["NPC_3040"],
            "SQLITE": ["CC17", "netincome"]
        }
        # 內部或外部 LLM
        self.mode_options = ['內部LLM', '外部LLM']
        # 內部 LLM 選項
        self.llm_options_internal = ["Qwen2-Alibaba", "Taiwan-llama3-8b", "Taiwan-llama2-13b"]
        # 外部 LLM 選項
        self.llm_options_external = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-35-turbo"]
        # 內部嵌入模型選項
        self.embedding_options_internal = ["llama3", "bge-m3"]
        # 外部嵌入模型選項
        self.embedding_options_external = ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]

    def display(self):
        """顯示側邊欄"""
        with st.sidebar:
            self._set_sidebar_button_style()  # 設定側邊欄按鈕樣式
            self._new_chat_button()  # 顯示新聊天按鈕
            self._agent_selection()  # 顯示助理類型選擇
            self._llm_selection()  # 顯示 LLM 模式選項
            self._embedding_selection()  # 顯示 Embedding 選項（依據助理類型選擇）
            self._chat_history_buttons()  # 顯示聊天記錄按鈕

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
        """, unsafe_allow_html=True)

    def _new_chat_button(self):
        """顯示新聊天按鈕"""
        if st.button("New Chat"):
            st.session_state['agent'] = '一般助理'
            # 點擊按鈕後，啟動新的聊天
            self.controller.new_chat()

    def _agent_selection(self):
        """顯示助理類型選擇與資料庫選擇"""
        st.title("Agent")

        current_agent = st.session_state.get('agent')  # 取得當前的助理類型
        selected_agent_index = self.agent_options.index(current_agent)  # 取得當前助理類型在選項中的索引位置

        selected_agent = st.radio(
            "請選擇助理種類型:",
            self.agent_options,  # 助理類型選項列表
            index=selected_agent_index  # 預設選擇當前助理類型
        )
        print('1. select', selected_agent)
        print('2. get', st.session_state.get('agent'))

        # 如果選擇的助理類型改變
        if selected_agent != st.session_state.get('agent'):
            # 開啟新的聊天窗口
            self.controller.new_chat()
            st.session_state['agent'] = selected_agent
            print('---selected_agent != st.session_state.get(agent)---')
            #st.rerun()  # 刷新頁面

        # 顯示資料庫選項
        if selected_agent not in ['一般助理', '個人KM']:
            self._database_selection()

    def _database_selection(self):
        """根據選擇的助理類型顯示資料庫選項"""
        # 建立資料來源選擇框
        self._create_selectbox('選擇資料來源:', 'db_source', self.db_source_options)

        # 根據選擇的資料來源顯示對應的資料庫選項
        db_source = st.session_state['db_source']
        db_name = self.db_name.get(db_source, ['na'])

        # 建立資料庫選擇框
        self._create_selectbox('選擇資料庫:', 'db_name', db_name)

    def _llm_selection(self):
        """顯示 LLM 模式選項"""
        st.title("LLM")

        current_mode = st.session_state.get('mode')  # 取得當前的助理類型
        selected_mode_index = self.mode_options.index(current_mode)  # 取得當前助理類型在選項中的索引位置

        selected_mode = st.radio(
            "LLM類型:",
            self.mode_options,  # 助理類型選項列表
            index=selected_mode_index  # 預設選擇當前助理類型
        )

        st.session_state['mode'] = selected_mode

        # 如果選擇的助理類型改變
        #if selected_mode != st.session_state.get('mode'):
        #    st.session_state['mode'] = selected_mode
            # 開啟新的聊天窗口
        #    self.controller.new_chat()

        # 根據選擇的 LLM 類型顯示對應的 LLM 選項
        if st.session_state.get('mode') == '內部LLM':
            llm_options = self.llm_options_internal
        else:
            llm_options = self.llm_options_external

        # 建立 LLM 選擇框
        self._create_selectbox('選擇 LLM：', 'llm_option', llm_options)

    def _embedding_selection(self):
        """顯示 Embedding 模式選項"""
        # 僅當助理類型為 '個人KM' 時顯示嵌入模型選項
        if st.session_state.get('agent') == '個人KM':
            st.title("Embedding")
            # 根據選擇的 LLM 顯示對應的嵌入模型選項
            if st.session_state.get('mode') == '內部LLM':
                embedding_options = self.embedding_options_internal
            else:
                embedding_options = self.embedding_options_external

            # 建立嵌入模型選擇框
            self._create_selectbox('選擇嵌入模型：', 'embedding', embedding_options)

    def _chat_history_buttons(self):
        """顯示側邊欄中的聊天記錄"""
        st.title("聊天記錄")
        # 取得當前聊天窗口的總數量
        total_windows = st.session_state.get('num_chat_windows')

        for index in range(total_windows):
            chat_title = self.controller.get_title(index)  # 取得聊天窗口的標題
            chat_window, delete_button = st.columns([4, 1])  # 設置標題和刪除按鈕的佈局

            # 點擊標題來選擇聊天窗口
            if chat_window.button(chat_title, key=f'chat_window_select_{index}'):
                st.session_state['active_window_index'] = index
                self._update_window_setup()

            # 點擊刪除按鈕來刪除聊天
            if delete_button.button("X", key=f'chat_delete_{index}'):
                # 刪除聊天並更新索引
                self.controller.delete_chat_history_and_update_indexes(index)
                self._update_active_window_index(index, total_windows)
                self._update_window_setup()

    def _update_active_window_index(self, deleted_index, total_windows):
        """更新目前活動窗口的索引"""
        active_window_index = st.session_state.get('active_window_index')
        # 如果刪除的窗口在當前活動窗口之前，則將索引 -1
        if active_window_index > deleted_index:
            st.session_state['active_window_index'] -= 1
        # 如果刪除的窗口就是當前活動窗口，則將索引設為最後一個窗口
        elif active_window_index == deleted_index:
            st.session_state['active_window_index'] = total_windows - 1

    def _update_window_setup(self):
        """更新窗口設定並重新執行應用程式"""
        index = st.session_state.get('active_window_index')
        # 取得當前活動窗口的設定
        self.userRecords_db.get_active_window_setup(index)
        st.rerun()  # 重新執行應用程式

    def _create_selectbox(self, label, key, options):
        """建立選擇框並更新 session state"""
        try:
            selected_index = options.index(st.session_state.get(key, options[0]))
        except ValueError:
            selected_index = 0
        # 根據選擇框選擇的值更新 session state
        st.session_state[key] = st.selectbox(label, options, index=selected_index)
