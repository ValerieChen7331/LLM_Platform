import streamlit as st
import pandas as pd
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

from apis.llm_api import LLMAPI
from apis.file_paths import FilePaths
from models.database_model import DatabaseModel

class LLMModel:
    def __init__(self):
        # 初始化文件路徑
        self.file_paths = FilePaths()
        self.output_dir = self.file_paths.get_output_dir()

        # 獲取會話狀態中的模型、API 基本 URL 和 API 金鑰
        self.model = st.session_state.get('model')
        self.api_base = st.session_state.get('api_base')
        self.api_key = st.session_state.get('api_key')

        self.database_model = DatabaseModel()

    def set_window_title(self, query):
    # 直接查詢 LLM
        try:
            llm = LLMAPI.get_llm()
            prompt_template = self._get_title_prompt()
            formatted_prompt = prompt_template.format(query=query)
            # 調用 LLM 模型獲取答案
            title = llm.invoke(formatted_prompt)

            print('------formatted_prompt------')
            print(formatted_prompt, title)
            return title

        except Exception as e:
            st.error(f"查詢 set_window_title 時發生錯誤: {e}")
            return "在查詢 set_window_title 時發生錯誤。"
    def query_llm_direct(self, query):
    # 直接查詢 LLM
        try:
            llm = LLMAPI.get_llm()
            prompt_template = self._get_llm_direct_prompt()
            chat_history = st.session_state.get('messages', [])
            formatted_prompt = prompt_template.format(query=query, chat_history=chat_history)
            # 調用 LLM 模型獲取答案
            response = llm.invoke(formatted_prompt)

            print('------formatted_prompt------')
            print(formatted_prompt, response)
            self.save_to_database(query, response)
            return response

        except Exception as e:
            st.error(f"查詢 LLM 時發生錯誤: {e}")
            return "在查詢 LLM 時發生錯誤。"

    def query_llm_rag(self, retriever, query):
    # 使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。
        try:
            # 創建 ConversationalRetrievalChain 實例
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=LLMAPI.get_llm(),
                retriever=retriever,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": self._get_rag_prompt()}
            )

            # 獲取聊天歷史
            chat_history = st.session_state.get('messages', [])

            # 調用 LLM 模型獲取答案
            result_rag = qa_chain.invoke({
                'question': query,
                'chat_history': chat_history
            })

            # 獲取檢索到的文件
            retrieved_documents = result_rag.get('source_documents', [])
            # 獲取答案
            response = result_rag.get('answer', '')

            self._save_retrieved_data_to_csv(query, retrieved_documents, response)
            print('------result_rag------')
            print(result_rag)
            self.save_to_database(query, response)
            return response, retrieved_documents

        except Exception as e:
            st.error(f"查詢 LLM 時發生錯誤: {e}")
            return "在查詢 LLM 時發生錯誤。", []

    def _get_title_prompt(self):
    # 直接查詢 LLM 的提示模板
        template = """
        根據以下問題，輸出一個關鍵字或標題。
        問題: {query}
        """
        return PromptTemplate(input_variables=["query"], template=template)

    def _get_llm_direct_prompt(self):
    # 直接查詢 LLM 的提示模板
        template = """
        若無特別說明，請使用繁體中文來回答。
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        問答歷史紀錄: {chat_history}
        問題: {query}
        """
        return PromptTemplate(input_variables=["query", "chat_history"], template=template)

    def _get_rag_prompt(self):
    # RAG 查詢 LLM 的提示模板
        template = """
        請根據「文件內容」回答問題。如果以下資訊不足，請如實告知，勿自行編造!
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        若無特別說明，請使用繁體中文來回答問題。：
        問答歷史紀錄: {chat_history}
        文件內容: {context}
        問題: {question}
        答案:
        """
        return PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)

    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
    # 保存檢索到的數據到 CSV 文件
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir.joinpath('retrieved_data.csv')

        # 將每個檢索到的文檔內容格式化為字符串
        context = "\n\n".join([
            f"文檔 {i + 1}:\n{chunk}" for i, chunk in enumerate(retrieved_data)
        ])
        #context = ""
        #for i, retrieved_chunk in enumerate(retrieved_data):  # 修正拼寫錯誤
        #    context += f"文檔 {i + 1}:\n{retrieved_chunk}\n\n"  # 添加換行符來分隔文檔

        # 準備新數據
        new_data = {
            "Question": [query],
            "Context": [context],
            "Response": [response]
        }
        new_df = pd.DataFrame(new_data)

        if output_file.exists():
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    def save_to_database(self, query, response):
        # 從 session state 中獲取模式、當前模型和當前聊天索引
        mode = st.session_state['mode']
        model = st.session_state['model']
        current_chat_window_index = st.session_state['current_chat_window_index']
        title = st.session_state['title']
        # 將新記錄插入到資料庫中
        self.database_model.execute_query(
                "INSERT INTO chat_history (conversation_id, mode, model, chat_window_index, user_query, ai_response, title) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (st.session_state['conversation_id'], mode, model, current_chat_window_index, query, response, title))




