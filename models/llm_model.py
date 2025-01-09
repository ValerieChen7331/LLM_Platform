import streamlit as st
import pandas as pd
import logging

from apis.llm_api import LLMAPI
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths

from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ChatMessageHistory

from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate

class LLMModel:
    def __init__(self):
        # 初始化文件路徑和資料庫模型
        self.file_paths = FilePaths()
        self.output_dir = self.file_paths.get_output_dir()
        self.vector_store_dir = self.file_paths.get_local_vector_store_dir()
        self.embedding_function = EmbeddingAPI.get_embedding_function()

        # 獲取會話狀態中的模型、API 基本 URL 和 API 金鑰
        self.model = st.session_state.get('model')
        self.api_base = st.session_state.get('api_base')
        self.api_key = st.session_state.get('api_key')

    def query_llm_direct(self, query):
        # 獲取 active_window_index
        active_window_index = st.session_state.get('active_window_index', 0)

        # 確保 session_state 中有針對 active_window_index 的 'conversation_memory'
        memory_key = f'conversation_memory_{active_window_index}'
        if memory_key not in st.session_state:
            st.session_state[memory_key] = ConversationBufferMemory(memory_key="history", input_key="input")

        # 使用 ChatMessageHistory 添加對話歷史到 ConversationBufferMemory
        chat_history_data = st.session_state.get('chat_history', [])
        if chat_history_data:
            chat_history = ChatMessageHistory()
            for record in chat_history_data:
                user_query, ai_response = record['user_query'], record['ai_response']
                chat_history.add_user_message(user_query)
                chat_history.add_ai_message(ai_response)

            # 將 ChatMessageHistory 設置為 ConversationBufferMemory 的歷史記錄
            st.session_state[memory_key].chat_memory = chat_history

        # 定義 LLM
        llm = LLMAPI.get_llm()

        # 自訂提示模板，包含上下文和指令
        init_prompt = f"""
        You are a helpful and knowledgeable assistant. You will provide responses in Traditional Chinese (台灣中文).
        Here is the conversation history:
        {{history}}

        Now, please provide a concise and relevant response to the following query:
        {{input}}
        """

        # 使用 RunnableWithMessageHistory 並確保 memory_key 和 prompt 中的變數一致
        conversation_chain = ConversationChain(
            llm=llm,
            memory=st.session_state[memory_key],
            prompt=ChatPromptTemplate.from_template(init_prompt)
        )
        # 查詢 LLM 並返回結果
        result = conversation_chain.invoke(input=query)
        response = result.get('response', '')
        print('-----------------')
        print(type(response))
        print(response)
        return response

    def set_window_title(self, query):
        """使用 LLM 根據用戶的查詢設置窗口標題。"""
        try:
            llm = LLMAPI.get_llm()          # 獲取 LLM API 物件
            prompt_template = self._title_prompt()   # 獲取prompt模板
            formatted_prompt = prompt_template.format(query=query)  # 格式化prompt模板，插入query

            title = llm.invoke(formatted_prompt)    # 調用 LLM 生成 window title
            if st.session_state.get('mode') == '內部LLM':
                pass
            else:
                title = title.content
            st.session_state['title'] = title
            return title

        except Exception as e:
            return st.error(f"查詢 set_window_title 時發生錯誤: {e}")

    def _title_prompt(self):
        """生成設置窗口標題所需的提示模板。"""
        template = """
        根據以下提問(Q:)，列出1個關鍵字。請務必遵守以下規則：
        1.只能輸出關鍵字，不要有其他說明。
        2.輸出字數12字以內。
        ---
        範例: 
        Q:如果有超過一個月的出勤獎勵，該如何計算？
        出勤獎勵
        ---
        Q: {query}        
        """
        return PromptTemplate(input_variables=["query"], template=template)


