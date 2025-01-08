import streamlit as st
import pandas as pd
import sqlite3
import logging

from langchain_core.runnables import RunnableWithMessageHistory

from apis.llm_api import LLMAPI
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths

from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate

from langchain.chains import ConversationChain
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ChatMessageHistory

from langchain.chains import (
        create_history_aware_retriever,
        create_retrieval_chain,
    )
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain.chains.question_answering import load_qa_chain
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

    def query_llm_rag_1(self, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        try:
            # 建立向量資料庫和檢索器
            vector_db = Chroma(
                embedding_function=self.embedding_function,
                persist_directory=self.vector_store_dir.as_posix()
            )
            retriever = vector_db.as_retriever(search_kwargs={'k': 3})
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=LLMAPI.get_llm(),           # 獲取 LLM API 物件
                retriever=retriever,            # 設置檢索器
                return_source_documents=True,   # 返回檢索到的文件
                combine_docs_chain_kwargs={"prompt": self._rag_prompt()}  # prompt 模板
            )

            # !!修改 chat_history!
            chat_history = []
            # 使用 RAG 查詢 LLM，生成答案
            result_rag = qa_chain.invoke({'question': query, 'chat_history': chat_history})

            response = result_rag.get('answer', '')  # 取得回答
            retrieved_documents = result_rag.get('source_documents', [])  # 取得檢索到的文件

            # 保存檢索到的數據到 CSV 文件
            self._save_retrieved_data_to_csv(query, retrieved_documents, response)
            return response, retrieved_documents

        except Exception as e:
            return self._handle_error(f"查詢 query_llm_rag 時發生錯誤: {e}"), []

    def query_llm_rag(self, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        try:
            # 初始化語言模型，使用 "gpt-3.5-turbo" 模型，溫度設為 0，確保回答穩定
            llm = LLMAPI.get_llm()

            # 建立向量資料庫和檢索器
            # embeddings_on_local_vectordb(self, document_chunks)
            # llm_model
            vector_db = Chroma.from_documents(embedding=self.embedding_function)

            # llm_model
            retriever = vector_db.as_retriever(search_kwargs={'k': 3})

            ### 將問題與上下文整合 ###
            # 系統提示，用於重構問題，考慮到聊天記錄，讓問題可以獨立理解
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

            # 創建具備聊天記錄感知能力的檢索器
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever, contextualize_q_prompt
            )

            ### 回答問題 ###
            # 系統提示，用於回答問題，根據檢索到的上下文進行回答
            qa_system_prompt = """
                您是回答問題的助手。\
                使用以下檢索到的內容來回答問題。\
                如果您不知道答案，請直接說您不知道。    
                {context}
            """
            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", qa_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )

            # 創建問題回答鏈
            question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

            # 建立檢索增強生成（RAG）的問答鏈
            rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

            ### 管理聊天記錄 ###
            # 狀態管理聊天記錄的儲存

            chat_history_data = st.session_state.get('chat_history', [])
            if chat_history_data:
                chat_history = ChatMessageHistory()
                for record in chat_history_data:
                    user_query, ai_response = record['user_query'], record['ai_response']
                    chat_history.add_user_message(user_query)
                    chat_history.add_ai_message(ai_response)
            else:

            # 創建具聊天記錄功能的檢索增強生成鏈，包含輸入與歷史訊息的關聯
            conversational_rag_chain = RunnableWithMessageHistory(
                rag_chain,
                chat_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer",
            )


            response = result_rag.get('answer', '')  # 取得回答
            retrieved_documents = result_rag.get('source_documents', [])  # 取得檢索到的文件

            # 保存檢索到的數據到 CSV 文件
            self._save_retrieved_data_to_csv(query, retrieved_documents, response)
            return response, retrieved_documents

        except Exception as e:
            return self._handle_error(f"查詢 query_llm_rag 時發生錯誤: {e}"), []

    def query_llm_rag(self, query):
        # 初始化 Vector DB 和 Retriever
        vector_db = Chroma(
            embedding_function=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        retriever = vector_db.as_retriever(search_kwargs={'k': 3})

        # 定義 LLM 和 prompt
        llm = LLMAPI.get_llm()
        prompt = "Your prompt structure here, e.g., 'Question: {input}\nContext: {retrieved_context}'"

        # 獲取 chat_history
        chat_history = st.session_state.get('chat_history', [])

        # 定義 get_session_history 函數
        def get_session_history():
            return chat_history

        # 定義 runnable 函數
        def runnable(query, context):
            return llm.generate(prompt.format(input=query, retrieved_context=context))

        # 構建 RunnableWithMessageHistory 實例
        runnable_with_history = RunnableWithMessageHistory(
            runnable=runnable,
            get_session_history=get_session_history
        )

        # 使用 retriever 取得相關文件
        context = retriever.retrieve(query)

        # 查詢 LLM 並更新 chat_history
        response = runnable_with_history.run(query=query, retrieved_context=context)
        chat_history.append({'user_query': query, 'ai_response': response})

        print(response)
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

