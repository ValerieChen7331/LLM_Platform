from services.llm_services import LLMService
from services.document_services import DocumentService
from models.database_model import DatabaseModel
import streamlit as st
import uuid
import pandas as pd

class UIController:
    def __init__(self):
        # 初始化 LLMService 和 DocumentService
        self.llm_service = LLMService()
        self.doc_service = DocumentService()
        self.database_model = DatabaseModel()

    def initialize_session_state(self):
        # 初始化 session 狀態
        database = self.database_model.load_database()
        check_history = not database.empty
        if check_history:
            count_chat_windows = len(set(database['chat_window_index']))
            st.session_state.setdefault('chat_window_index', count_chat_windows)
            st.session_state.setdefault('current_chat_window_index', count_chat_windows)
        else:
            st.session_state.setdefault('chat_window_index', 0)
            st.session_state.setdefault('current_chat_window_index', 0)

            # 初始化 session 狀態
        st.session_state.setdefault('mode', '內部LLM')
        st.session_state.setdefault('model', None)
        st.session_state.setdefault('option', None)
        st.session_state.setdefault('messages', [])
        st.session_state.setdefault('retriever', None)
        st.session_state.setdefault('api_base', None)
        st.session_state.setdefault('api_key', None)
        st.session_state.setdefault('current_model', None)
        st.session_state.setdefault('conversation_id', str(uuid.uuid4()))
        st.session_state.setdefault('chat_history', [])
        st.session_state.setdefault('title', '')
        return check_history


    #def new_chat(self):
        # 開啟新聊天
        # current_model = st.session_state.get('current_model', '')  # 獲取當前選定的模型，如果沒有設定則預設為空字串
        #st.session_state['conversation_id'] = str(uuid.uuid4())  # 生成一個新的唯一對話 ID 並存儲在 session_state 中
        #if current_model:
            # 檢查 session_state 中是否存在該模型對應的聊天記錄，如果不存在則初始化一個空的聊天記錄列表
            #if current_model not in st.session_state['chat_history'][st.session_state['mode']]:
             #   st.session_state['chat_history'][st.session_state['mode']][current_model] = []
            # 將一個新的空聊天會話列表追加到對應的模型的聊天記錄中
            #st.session_state['chat_history'][st.session_state['mode']][current_model].append([])
            # 更新 current_chat_window_index 為新的聊天會話的索引
            #st.session_state['current_chat_window_index'] = len(
            #    st.session_state['chat_history'][st.session_state['mode']][current_model]) - 1
    def get_title(self, current_chat_window_index):
        # 從資料庫加載數據
        df_database = self.database_model.load_database()

        # 過濾出匹配 current_chat_window_index 的行
        df_window = df_database[df_database['chat_window_index'] == current_chat_window_index]

        # 如果找到匹配的行，將標題設置到 session_state 中
        if not df_window.empty:
            st.session_state['title'] = df_window['title'].iloc[0]
        else:
            # 若未找到匹配的行，處理這種情況
            st.session_state['title'] = "視窗 {current_chat_window_index}"

    def new_chat(self):
        st.session_state['conversation_id'] = str(uuid.uuid4())
        #st.session_state.get('current_model', '')

        st.session_state['chat_history'] = []
        #st.session_state['chat_history'].append([])
        print('-------new_chat chat_history-----------')
        print(st.session_state['chat_history'])

        st.session_state['chat_window_index'] += 1
        st.session_state['current_chat_window_index'] = st.session_state['chat_window_index']


    def if_change_mode(self, new_mode):
        # 切換模式
        if new_mode != st.session_state['mode']:
            st.session_state['mode'] = new_mode
            st.session_state['current_model'] = None
            st.session_state['current_chat_window_index'] = 0
            st.session_state['conversation_id'] = str(uuid.uuid4())

    def get_chat_history(self):
        try:
            # 獲取當前聊天窗口索引
            current_chat_window_index = st.session_state.get('current_chat_window_index')
            if current_chat_window_index is None:
                print("current_chat_window_index 為 None")
                st.session_state['chat_history'] = []
                return st.session_state['chat_history']

            # SQL 查詢
            sql_query = "SELECT id, conversation_id, chat_window_index, user_query, ai_response FROM chat_history WHERE chat_window_index = ? ORDER BY id"
            chat_history_database = self.database_model.fetch_query(sql_query, (current_chat_window_index,))

            # 檢查是否有資料返回
            if chat_history_database:
                df = pd.DataFrame(chat_history_database,
                                  columns=['id', 'conversation_id', 'chat_window_index', 'user_query', 'ai_response'])

                # 將當前聊天視窗索引和聊天歷史記錄儲存到 session state 中
                current_chat_history = df[['user_query', 'ai_response']].values.tolist()
                st.session_state['chat_history'] = current_chat_history
                return current_chat_history
            else:
                st.session_state['chat_history'] = []
                return st.session_state['chat_history']
        except sqlite3.OperationalError as e:
            # 處理資料庫操作錯誤
            print(f"資料庫操作錯誤: {e}")
            st.session_state['chat_history'] = []
            return st.session_state['chat_history']
        except Exception as e:
            # 處理其他錯誤
            print(f"發生錯誤: {e}")
            st.session_state['chat_history'] = []
            return st.session_state['chat_history']


    def delete_chat_history_and_update_indexes(self, delete_index):
        # delete_chat_history
        self.database_model.execute_query(
            "DELETE FROM chat_history WHERE chat_window_index = ?", (delete_index,))

        # update_indexes
        chat_histories = self.database_model.fetch_query(
            "SELECT id, chat_window_index FROM chat_history ORDER BY chat_window_index")

        for id, chat_window_index in chat_histories:
            if chat_window_index > delete_index:
                new_index = chat_window_index - 1
                self.database_model.execute_query(
                    "UPDATE chat_history SET chat_window_index = ? WHERE id = ?", (new_index, id))

        st.session_state['chat_window_index'] -= 1



    def handle_query(self, query):
        # 處理查詢
        st.chat_message("human").write(query)
        response = self.llm_service.query(query)
        st.chat_message("ai").write(response)
        self.llm_service.title(query)

    def display_messages(self):
        # 顯示消息
        for message in st.session_state['messages']:
            st.chat_message('human').write(message[0])
            st.chat_message('ai').write(message[1])

    def display_chat_history(self):
        # 顯示聊天歷史
        with st.sidebar:
            st.title("聊天歷史")
            for mode, models in st.session_state['chat_history'].items():
                for model, chats in models.items():
                    st.write(f"{mode} - {model}: {len(chats)} chats")

    def process_uploaded_documents(self):
        # 處理上傳的文件
        self.doc_service.process_uploaded_documents()



#---------------------
# mock_controller.py
class MockUIController:
    def new_chat(self):
        print("Mock new_chat called")

    def if_change_mode(self, new_mode):
        print(f"Mock if_change_mode called with mode: {new_mode}")
        # 模擬更改模式後的 session state
        st.session_state['mode'] = new_mode

    def get_chat_history(self):
        print("Mock get_chat_history called")
        # 返回一些假數據以模擬聊天記錄
        return [
            [("用戶消息 1", "AI 回應 1")],
            [("用戶消息 2", "AI 回應 2")]
        ]

    def delete_chat(self, index):
        print(f"Mock delete_chat called with index: {index}")

    def initialize_session_state(self):
        print("Mock initialize_session_state called")
        # 初始化 session state
        st.session_state['mode'] = '內部LLM'
        st.session_state['messages'] = []
        st.session_state['current_chat_window_index'] = 0

    def process_uploaded_documents(self):
        print("Mock process_uploaded_documents called")

    def handle_query(self, query):
        print(f"Mock handle_query called with query: {query}")
        # 模擬處理查詢後的回應
        st.session_state['messages'].append((query, "這是 AI 的回應"))

    def load_chat_history(self):
        print("Mock load_chat_history called")
        # 返回一些假數據以模擬聊天記錄
        return [("用戶消息 1", "AI 回應 1"), ("用戶消息 2", "AI 回應 2")]

    def delete_chat_history_and_update_indexes(self, mode, model, delete_index):
        print("Mock delete_chat_history_and_update_indexes")


