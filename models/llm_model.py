import streamlit as st
import pandas as pd
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

from apis.llm_api import LLMAPI
from apis.file_paths import FilePaths


class LLMModel:
    def __init__(self):
        # 初始化文件路徑和資料庫模型
        self.file_paths = FilePaths()
        self.output_dir = self.file_paths.get_output_dir()

        # 獲取會話狀態中的模型、API 基本 URL 和 API 金鑰
        self.model = st.session_state.get('model')
        self.api_base = st.session_state.get('api_base')
        self.api_key = st.session_state.get('api_key')

    def set_window_title(self, query):
        """使用 LLM 根據用戶的查詢設置窗口標題。"""
        try:
            llm = LLMAPI.get_llm()
            prompt_template = self._get_title_prompt()
            formatted_prompt = prompt_template.format(query=query)

            title = llm.invoke(formatted_prompt)
            st.session_state['title'] = title

            return title

        except Exception as e:
            return self._handle_error(f"查詢 set_window_title 時發生錯誤: {e}")

    def query_llm_direct(self, query):
        """直接查詢 LLM 並返回結果。"""
        try:
            llm = LLMAPI.get_llm()
            prompt_template = self._get_llm_direct_prompt()
            # !!修改 chat_history!
            chat_history = []
            formatted_prompt = prompt_template.format(query=query, chat_history=chat_history)

            response = llm.invoke(formatted_prompt)
            return response

        except Exception as e:
            return self._handle_error(f"查詢 query_llm_direct 時發生錯誤: {e}")

    def query_llm_rag(self, retriever, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        try:
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=LLMAPI.get_llm(),
                retriever=retriever,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": self._get_rag_prompt()}
            )

            # !!修改 chat_history!
            chat_history = []
            result_rag = qa_chain.invoke({'question': query, 'chat_history': chat_history})

            response = result_rag.get('answer', '')
            retrieved_documents = result_rag.get('source_documents', [])

            self._save_retrieved_data_to_csv(query, retrieved_documents, response)
            return response, retrieved_documents

        except Exception as e:
            return self._handle_error(f"查詢 query_llm_rag 時發生錯誤: {e}"), []

    def _get_title_prompt(self):
        """生成設置窗口標題所需的提示模板。"""
        template = """
        根據以下提問(Q:)，列出1個關鍵字(A:)。請務必遵守以下規則：
        1.只能輸出關鍵字，不要有其他說明。
        2.若使用者的提問字數少於5，直接輸出提問。
        3.輸出字數12字以內。
        ---
        範例: 
        Q:如果有超過一個月的出勤獎勵，該如何計算？
        A:出勤獎勵
        ---
        Q: {query}
        A:
        """
        return PromptTemplate(input_variables=["query"], template=template)

    def _get_llm_direct_prompt(self):
        """生成直接查詢 LLM 所需的提示模板。"""
        template = """
        若無特別說明，請使用繁體中文來回答。
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        問答歷史紀錄: {chat_history}
        問題: {query}
        """
        return PromptTemplate(input_variables=["query", "chat_history"], template=template)

    def _get_rag_prompt(self):
        """生成 RAG 查詢 LLM 所需的提示模板。"""
        template = """
        請根據「文件內容」回答問題。如果以下資訊不足，請如實告知，勿自行編造!
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        若無特別說明，請使用繁體中文來回答問題：
        問答歷史紀錄: {chat_history}
        文件內容: {context}
        問題: {question}
        答案:
        """
        return PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)

    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
        """將檢索到的數據保存到 CSV 文件中。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir.joinpath('retrieved_data.csv')

        context = "\n\n".join([f"文檔 {i + 1}:\n{chunk}" for i, chunk in enumerate(retrieved_data)])
        new_data = {"Question": [query], "Context": [context], "Response": [response]}
        new_df = pd.DataFrame(new_data)

        if output_file.exists():
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    def _handle_error(self, message):
        """處理並顯示錯誤信息。"""
        st.error(message)
        return message
