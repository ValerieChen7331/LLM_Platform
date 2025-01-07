import streamlit as st
from services.llm_services import LLMService
from services.document_services import DocumentService

class UIController:
    def __init__(self):
        self.llm_service = LLMService()
        self.doc_service = DocumentService()

    def configure_page(self):
        st.set_page_config(page_title="南亞塑膠GenAI")
        st.title("南亞塑膠GenAI")

    def initialize_session_state(self):
        st.session_state.setdefault('mode', '內部LLM')
        st.session_state.setdefault('messages', [])
        st.session_state.setdefault('chat_history', [])
        st.session_state.setdefault('retriever', None)

    def select_llm_type(self):
        with st.sidebar:
            st.title("選項")
            st.session_state['mode'] = st.radio("LLM 類型：", ('內部LLM', '外部LLM'))

            if st.session_state['mode'] == '內部LLM':
                options = [
                    "qwen2:7b",
                    "SimonPu/llama-3-taiwan-8b-instruct-dpo",
                    "wangrongsheng/taiwanllm-13b-v2.0-chat",
                    "wangshenzhi/gemma2-9b-chinese-chat"
                ]
                st.session_state['model'] = st.selectbox('選擇一個選項：', options)
                st.session_state['api_base'] = 'http://10.5.61.81:11434'
                st.session_state['api_key'] = 'None'
            else:
                st.session_state['api_base'] = st.text_input('API 地址：', type='password')
                st.session_state['api_key'] = st.text_input('API 密鑰：', type='password')

    def input_fields(self):
        st.session_state['source_docs'] = st.file_uploader(label="上傳文檔", type="pdf", accept_multiple_files=True)

    def handle_query(self, query):
        st.chat_message("human").write(query)
        response = self.llm_service.query(query)
        st.chat_message("ai").write(response)

        st.session_state['messages'].append((query, response))
        st.session_state['chat_history'].append(f"User: {query}")
        st.session_state['chat_history'].append(f"AI: {response}")

    def display_messages(self):
        for message in st.session_state['messages']:
            st.chat_message('human').write(message[0])
            st.chat_message('ai').write(message[1])

    def display_chat_history(self):
        with st.sidebar:
            st.title("聊天歷史")
            for chat in st.session_state['chat_history']:
                st.write(chat)

    def process_uploaded_documents(self):
        self.doc_service.process_uploaded_documents()
