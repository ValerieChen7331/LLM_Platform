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

    def set_window_title(self, query):
        """使用 LLM 根據用戶的查詢設置窗口標題。"""
        try:
            llm = LLMAPI.get_llm()          # 獲取 LLM API 物件
            prompt_template = self._title_prompt()   # 獲取prompt模板
            formatted_prompt = prompt_template.format(query=query)  # 格式化prompt模板，插入query

            title = llm.invoke(formatted_prompt)    # 調用 LLM 生成 window title
            st.session_state['title'] = title
            return title

        except Exception as e:
            return self._handle_error(f"查詢 set_window_title 時發生錯誤: {e}")

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
        return response

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

    def _llm_direct_prompt(self):
        """生成直接查詢 LLM 所需的提示模板。"""
        template = """
        若無特別說明，請使用繁體中文來回答。
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        問答歷史紀錄: {chat_history}
        問題: {query}
        """
        return PromptTemplate(input_variables=["query", "chat_history"], template=template)

    def _rag_prompt(self):
        """生成 RAG 查詢 LLM 所需的提示模板。"""
        template = """
        請根據「文件內容」回答問題。如果以下資訊不足，請如實告知，勿自行編造!
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        若無特別說明，請使用繁體中文來回答問題：        
        文件內容: {context}
        問題: {question}
        答案:
        """
        # 問答歷史紀錄: {chat_history}
        return PromptTemplate(input_variables=["context", "question"], template=template)


    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
        """將檢索到的數據保存到 CSV 文件中。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)  # 確保輸出目錄存在
        output_file = self.output_dir.joinpath('retrieved_data.csv')  # 定義輸出文件路徑

        # 組合檢索到的文件內容
        context = "\n\n".join([f"文檔 {i + 1}:\n{chunk}" for i, chunk in enumerate(retrieved_data)])
        new_data = {"Question": [query], "Context": [context], "Response": [response]}  # 新數據
        new_df = pd.DataFrame(new_data)  # 將新數據轉換為 DataFrame

        if output_file.exists():
            existing_df = pd.read_csv(output_file)  # 如果文件已存在，讀取現有數據
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)  # 合併現有數據和新數據
        else:
            combined_df = new_df  # 否則僅使用新數據

        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')  # 保存數據到 CSV 文件

    def _handle_error(self, message):
        """處理並顯示錯誤信息，並記錄日誌。"""
        logging.error(message)  # 記錄錯誤信息到日誌
        st.error(message)  # 在 Streamlit 前端顯示錯誤信息
        return message  # 返回錯誤信息

