import streamlit as st
import pandas as pd

from apis.llm_api import LLMAPI
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths

from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ChatMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

class RAGModel:
    def __init__(self):
        # 初始化文件路徑和嵌入函數
        self.file_paths = FilePaths()
        self.output_dir = self.file_paths.get_output_dir()
        self.embedding_function = EmbeddingAPI.get_embedding_function()

    def query_llm_rag(self, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        try:
            # 初始化語言模型，使用 "gpt-3.5-turbo" 模型，溫度設為 0，確保回答穩定
            llm = LLMAPI.get_llm()

            # 建立向量資料庫和檢索器
            vector_db = Chroma.from_documents(embedding=self.embedding_function)
            retriever = vector_db.as_retriever(search_kwargs={'k': 3})

            # 創建具備聊天記錄感知能力的檢索器
            history_aware_retriever = self._create_history_aware_retriever(llm, retriever)

            # 創建具聊天記錄功能的檢索增強生成鏈
            conversational_rag_chain = self._create_conversational_rag_chain(history_aware_retriever)

            # 查詢 RAG，並獲取回答和檢索到的文件
            result_rag = conversational_rag_chain.run({
                'input': query,
                'chat_history': self._get_chat_history_from_session(),
            })

            response = result_rag.get('answer', '')  # 取得回答
            retrieved_documents = result_rag.get('source_documents', [])  # 取得檢索到的文件

            # 保存檢索到的數據到 CSV 文件
            self._save_retrieved_data_to_csv(query, retrieved_documents, response)

            return response, retrieved_documents

        except Exception as e:
            # 當發生錯誤時顯示錯誤訊息
            return st.error(f"查詢 query_llm_rag 時發生錯誤: {e}"), []

    def _create_history_aware_retriever(self, llm, retriever):
        """創建具備聊天記錄感知能力的檢索器。"""
        contextualize_q_system_prompt = """
            根據聊天記錄和最新的使用者問題，\
            該問題可能參考了聊天記錄中的上下文，請將其重構為一個可以不依賴聊天記錄就能理解的問題。\
            不要回答問題，只需重新表述，若無需表述則保持不變。
        """
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        # 使用 LLM 和檢索器來創建具歷史感知的檢索器
        return create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    def _create_conversational_rag_chain(self, history_aware_retriever):
        """創建具聊天記錄功能的檢索增強生成鏈。"""
        qa_system_prompt = """
            您是回答問題的助手。\
            使用以下檢索到的內容來回答問題。\
            如果您不知道答案，請直接說您不知道。\
            {context}
        """
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        # 創建一個問題回答鏈，並與檢索增強生成鏈結合
        question_answer_chain = create_stuff_documents_chain(LLMAPI.get_llm(), qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # 創建具聊天記錄功能的檢索增強生成鏈
        return RunnableWithMessageHistory(
            rag_chain,
            self._get_chat_history_from_session,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def _get_chat_history_from_session(self) -> ChatMessageHistory:
        """從 session state 中取得聊天記錄，若無則創建新的聊天記錄。"""
        # 從 session 中獲取聊天記錄，如果不存在，則初始化空的聊天記錄
        chat_history_data = st.session_state.get('chat_history', [])
        chat_history = ChatMessageHistory()
        for record in chat_history_data:
            user_query, ai_response = record['user_query'], record['ai_response']
            chat_history.add_user_message(user_query)
            chat_history.add_ai_message(ai_response)
        return chat_history

    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
        """將檢索到的數據保存到 CSV 文件中。"""
        # 確保輸出目錄存在，若不存在則創建
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir.joinpath('retrieved_data.csv')  # 定義輸出文件路徑

        # 將檢索到的文件內容組合
        context = "\n\n".join([f"文檔 {i + 1}:\n{chunk}" for i, chunk in enumerate(retrieved_data)])
        new_data = {"Question": [query], "Context": [context], "Response": [response]}  # 新數據
        new_df = pd.DataFrame(new_data)  # 將新數據轉換為 DataFrame

        if output_file.exists():
            # 如果文件已存在，讀取現有數據，並合併新數據
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            # 如果文件不存在，僅使用新數據
            combined_df = new_df

        # 將合併後的數據保存到 CSV 文件
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
