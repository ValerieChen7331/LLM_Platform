import streamlit as st
import pandas as pd
import sqlite3
import logging

from apis.llm_api import LLMAPI
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths

# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
# from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory

# from langchain.chains import ConversationChain
from langchain.chains import ConversationalRetrievalChain
# from langchain.memory import ConversationBufferMemory
# from langchain.memory import ChatMessageHistory

class RAGModel:
    def __init__(self, chat_session_data):
        # 初始化 hat_session_data
        self.chat_session_data = chat_session_data
        self.mode = chat_session_data.get("mode")
        self.llm_option = chat_session_data.get('llm_option')

        # 初始化文件路徑
        file_paths = FilePaths()
        self.output_dir = file_paths.get_output_dir()
        username = chat_session_data.get("username")
        conversation_id = chat_session_data.get("conversation_id")
        self.vector_store_dir = file_paths.get_local_vector_store_dir(username, conversation_id)


    def query_llm_rag(self, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        # 初始化語言模型
        llm = LLMAPI.get_llm(self.mode, self.llm_option)
        # 初始化 embedding 模型
        embedding = self.chat_session_data.get("embedding")
        embedding_function = EmbeddingAPI.get_embedding_function(self.mode, embedding)

        # 建立向量資料庫和檢索器
        vector_db = Chroma(
            embedding_function=embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        retriever = vector_db.as_retriever(search_kwargs={'k': 3})

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,  # 獲取 LLM API 物件
            retriever=retriever,  # 設置檢索器
            return_source_documents=True,  # 返回檢索到的文件
            combine_docs_chain_kwargs={"prompt": self._rag_prompt()}  # prompt 模板
        )

        # !!修改 chat_history!
        chat_history = []
        # 使用 RAG 查詢 LLM，生成答案
        result_rag = qa_chain.invoke({'question': query, 'chat_history': chat_history})

        response = result_rag.get('answer', '')  # 取得回答
        retrieved_documents = result_rag.get('source_documents', [])  # 取得檢索到的文件
        print('2. retrieved_documents: ', retrieved_documents)

        # 保存檢索到的數據到 CSV 文件
        self._save_retrieved_data_to_csv(query, retrieved_documents, response)
        return response, retrieved_documents

    def _rag_prompt(self):
        """生成 RAG 查詢 LLM 所需的提示模板。"""
        template = """
        請根據「文件內容」回答問題。如果以下資訊不足，請如實告知，勿自行編造!
        若無特別說明，請使用繁體中文來回答問題。
        文件內容: {context}
        問題: {question}
        答案:
        """
        return PromptTemplate(input_variables=["context", "question"], template=template)

    # def _get_chat_history_from_session(self) -> str:
    #     """從 session state 中取得聊天記錄，格式化為字符串形式."""
    #     chat_history_data = self.chat_session_data.get('chat_history', [])
    #     formatted_history = ""
    #     for record in chat_history_data:
    #         user_query = record['user_query']
    #         ai_response = record['ai_response']
    #         formatted_history += f"User: {user_query}\nAI: {ai_response}\n"
    #     return formatted_history

    def _get_chat_history_from_session(self) -> ChatMessageHistory:
        """從 session state 中取得聊天記錄，若無則創建新的聊天記錄。"""
        # 從 session 中獲取聊天記錄，如果不存在，則初始化空的聊天記錄
        chat_history_data = self.chat_session_data.get('chat_history', [])
        chat_history = ChatMessageHistory()
        for record in chat_history_data:
            user_query, ai_response = record['user_query'], record['ai_response']
            chat_history.add_user_message(user_query)
            chat_history.add_ai_message(ai_response)
        return chat_history

    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
        """將檢索到的數據保存到 CSV 文件中。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)  # 確保輸出目錄存在
        output_file = self.output_dir.joinpath('retrieved_data.csv')  # 定義輸出文件路徑

        # 組合檢索到的文件內容
        # context = "\n\n".join([f"文檔 {i + 1}:\n{chunk}" for i, chunk in enumerate(retrieved_data)])
        context = "\n\n".join([f"文檔 {i + 1}:\n{chunk.page_content}" for i, chunk in enumerate(retrieved_data)])

        new_data = {"Question": [query], "Context": [context], "Response": [response]}  # 新數據
        new_df = pd.DataFrame(new_data)  # 將新數據轉換為 DataFrame

        if output_file.exists():
            existing_df = pd.read_csv(output_file)  # 如果文件已存在，讀取現有數據
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)  # 合併現有數據和新數據
        else:
            combined_df = new_df  # 否則僅使用新數據

        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')  # 保存數據到 CSV 文件
