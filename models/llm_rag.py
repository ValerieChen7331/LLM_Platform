import streamlit as st
import pandas as pd

from apis.llm_api import LLMAPI
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths

#from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.vectorstores import FAISS

class RAGModel:
    def __init__(self):
        # 初始化文件路徑和嵌入函數
        self.file_paths = FilePaths()
        self.output_dir = self.file_paths.get_output_dir()
        self.vector_store_dir = self.file_paths.get_local_vector_store_dir()
        self.embedding_function = EmbeddingAPI.get_embedding_function()

    def query_llm_rag(self, query):
        """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
        try:
            answer_template = """
            Answer the question based only on the following context, which can include text, images and tables:
            {context}
            Question: {question} 
            """
            answer_chain = LLMChain(
                llm=LLMAPI.get_llm(),
                prompt=PromptTemplate.from_template(answer_template)
            )

            # 加載 FAISS 向量資料庫
            vectorstore = FAISS.load_local(
                self.vector_store_dir.as_posix(),
                embeddings=self.embedding_function,
                allow_dangerous_deserialization=True
            )

            # 使用向量資料庫進行相似度檢索
            relevant_docs = vectorstore.similarity_search(query, k=5)

            context = ""
            retrieved_documents = []  # 儲存檢索到的文件內容

            # 構建 context，並檢查每個文檔的類型
            for d in relevant_docs:
                if d.metadata.get('type') == 'text':
                    context += '[text]' + d.metadata.get('original_content', '')
                elif d.metadata.get('type') == 'table':
                    context += '[table]' + d.metadata.get('original_content', '')
                retrieved_documents.append(d)

            # 生成答案
            result = answer_chain.run({'context': context, 'question': query})
            response = result

            # 將檢索到的數據保存到 CSV 文件中
            self._save_retrieved_data_to_csv(query, retrieved_documents, response)

            # 打印結果，便於檢查
            print(result)

            # 返回答案與檢索到的文件
            return response, retrieved_documents

        except Exception as e:
            # 錯誤處理，顯示錯誤訊息並返回空結果
            st.error(f"查詢 query_llm_rag 時發生錯誤: {e}")
            return None, []

    def _save_retrieved_data_to_csv(self, query, retrieved_data, response):
        """將檢索到的數據保存到 CSV 文件中。"""
        # 確保輸出目錄存在，若不存在則創建
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir.joinpath('retrieved_data.csv')  # 定義輸出文件路徑

        # 組合檢索到的文件內容
        context = "\n\n".join([f"文檔 {i + 1}:\n{chunk.page_content}" for i, chunk in enumerate(retrieved_data)])
        new_data = {
            "Question": [query],
            "Context": [context],
            "Response": [response]
        }  # 新數據

        new_df = pd.DataFrame(new_data)  # 將新數據轉換為 DataFrame

        if output_file.exists():
            # 如果文件已存在，讀取現有數據並合併新數據
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            # 如果文件不存在，僅使用新數據
            combined_df = new_df

        # 將合併後的數據保存到 CSV 文件
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')