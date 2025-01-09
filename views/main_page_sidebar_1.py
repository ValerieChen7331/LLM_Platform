import streamlit as st
from models.batabase_userRecords import UserRecordsDB
from models.document_model import DocumentModel
class Sidebar:
    def __init__(self, controller):
        """初始化側邊欄物件"""
        self.controller = controller
        self.userRecords_db = UserRecordsDB()
        self.document_model = DocumentModel()

        self.agent_options = ['一般助理', '個人KM', '資料庫查找助理', '資料庫查找助理2.0', 'SQL生成助理']
        self.db_source_options = ["Oracle", "MSSQL", "SQLITE"]
        self.llm_options_internal = ["Qwen2-Alibaba", "Taiwan-llama3-8b", "Taiwan-llama2-13b"]
        self.llm_options_external = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-35-turbo"]
        self.embedding_options_internal = ["llama3", "bge-m3"]
        self.embedding_options_external = ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]

    def display(self):
        """顯示側邊欄"""
        with st.sidebar:
            self._set_sidebar_button_style()  # 設定側邊欄按鈕樣式
            self._new_chat_button()  # 顯示新聊天按鈕
            self._agent_selection()  # 顯示助理類型選擇
            self._llm_selection()  # 顯示 LLM 模式選項
            self._embedding_selection()  # 顯示 Embedding 選項（取決於助理類型）
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
        """, unsafe_allow_html=True)  # 使用 HTML 和 CSS 設定按鈕樣式

    def _new_chat_button(self):
        """顯示新聊天按鈕"""
        if st.button("New Chat"):
            st.session_state['agent'] = '一般助理'
            # 點擊按鈕後，啟動新的聊天
            self.controller.new_chat()

    def _create_selectbox(self, label, key, options):
        """建立選擇框並更新 session state"""
        try:
            selected_index = options.index(st.session_state.get(key, options[0]))
        except ValueError:
            selected_index = 0
        st.session_state[key] = st.selectbox(label, options, index=selected_index)

    def _create_radio(self, label, key, options):
        """建立單選框並更新 session state"""
        try:
            selected_index = options.index(st.session_state.get(key, options[0]))
        except ValueError:
            selected_index = 0
        st.session_state[key] = st.radio(label, options, index=selected_index)
        if st.session_state[key] != st.session_state.get(key):
            self.controller.new_chat()

    def _agent_selection(self):
        """顯示助理類型選擇與資料庫選擇"""
        st.title("Agent")

        current_agent = st.session_state.get('agent')  # 取得當前的助理類型
        selected_agent_index = self.agent_options.index(current_agent)  # 取得當前助理類型在選項中的索引位置
        self._create_radio("請選擇助理種類型:", 'agent', self.agent_options)

        selected_agent = st.radio(
            "請選擇助理種類型:",
            self.agent_options,  # 助理類型選項列表
            index=selected_agent_index  # 預設選擇當前助理類型
        )

        # 如果選擇的助理類型改變
        if selected_agent != st.session_state.get('agent'):
            st.session_state['agent'] = selected_agent
            # 開啟新的聊天窗口
            self.controller.new_chat()

        # 顯示資料庫選項
        if selected_agent not in ['一般助理', '個人KM']:
            self._database_selection()

    def _database_selection(self):
        """根據選擇的助理類型顯示資料庫選項"""

        # 取得資料來源對應的資料庫選項
        db_options = {
            "Oracle": ["v2nbfc00_xd_QMS"],
            "MSSQL": ["NPC_3040"],
            "SQLITE": ["CC17", "netincome"]
        }

        self._create_selectbox('選擇資料來源:', 'db_source', self.db_source_options)
        db_source = st.session_state['db_source']
        db_options = db_options.get(db_source, ['na'])
        self._create_selectbox('選擇資料庫:', 'db_name', db_options)

        self._create_selectbox('選擇資料庫:', 'db_options', db_options)

    def _llm_selection(self):
        """顯示 LLM 模式選項"""
        st.title("LLM")
        self._create_radio('LLM 類型:', 'mode', ['內部LLM', '外部LLM'])

        if st.session_state['mode'] == '內部LLM':
            llm_options = self.llm_options_internal
        else:
            llm_options = self.llm_options_external

        self._create_selectbox('選擇 LLM：', 'llm_option', llm_options)


    def _embedding_selection(self):
        """顯示 Embedding 模式選項"""
        """顯示 Embedding 模式選項"""
        if st.session_state.get('agent') == '個人KM':
            st.title("Embedding")

            if st.session_state['mode'] == '內部LLM':
                embedding_options = self.embedding_options_internal
            else:
                embedding_options = self.embedding_options_external

            self._create_selectbox('選擇嵌入模型：', 'embedding', embedding_options)

    def _chat_history_buttons(self):
        """顯示側邊欄中的聊天記錄"""
        st.title("聊天記錄")
        # 取得目前的聊天窗口數量
        total_windows = st.session_state.get('num_chat_windows')

        for index in range(total_windows):
            chat_title = self.controller.get_title(index)  # 取得聊天窗口的標題
            chat_window, delete_button = st.columns([4, 1])  # 設置標題和刪除按鈕

            # 點擊 window, 回到過去聊天紀錄的設定
            if chat_window.button(chat_title, key=f'chat_window_select_{index}'):
                st.session_state['active_window_index'] = index
                self._update_window_setup()

            if delete_button.button("X", key=f'chat_delete_{index}'):
                # 刪除聊天記錄並更新索引
                self.controller.delete_chat_history_and_update_indexes(index)
                # 更新目前活動的窗口索引
                self._update_active_window_index(index, total_windows)
                self._update_window_setup()

    def _update_active_window_index(self, deleted_index, total_windows):
        """更新目前視窗索引"""
        active_window_index = st.session_state.get('active_window_index')
        # 如果刪除的窗口在當前窗口前，則將索引 -1
        if active_window_index > deleted_index:
            st.session_state['active_window_index'] -= 1
        # 如果刪除的窗口就是當前活動窗口，則將索引設為最後一個窗口
        elif active_window_index == deleted_index:
            st.session_state['active_window_index'] = total_windows - 1

    def _update_window_setup(self):
        index = st.session_state.get('active_window_index')
        self.userRecords_db.get_active_window_setup(index)  # 取得聊天窗口設定
        st.rerun()  # 重新執行應用程



