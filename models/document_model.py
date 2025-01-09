import tempfile
import logging
from pathlib import Path

from unstructured.partition.pdf import partition_pdf
import streamlit as st
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import uuid
from langchain.schema import Document

from langchain_community.vectorstores import Chroma
from apis.embedding_api import EmbeddingAPI
from apis.file_paths import FilePaths
from apis.llm_api import LLMAPI


# PDF 處理類別，用於處理 PDF 文件的上傳、解析、摘要生成與嵌入向量庫
class DocumentModel:
    def __init__(self):
        # 初始化文件路徑和嵌入函數
        self.file_paths = FilePaths()
        self.tmp_dir = self.file_paths.get_tmp_dir()
        self.vector_store_dir = self.file_paths.get_local_vector_store_dir()
        self.embedding_function = EmbeddingAPI.get_embedding_function()

    def create_temporary_files(self):
        """建立臨時文件，並儲存上傳的 PDF 檔案"""
        # 確保臨時文件的目錄已存在，若不存在則創建該目錄
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        temporary_files = []  # 用來儲存臨時文件路徑的清單
        doc_names = {}  # 用來儲存原始文件名與臨時文件名的對應關係

        # 從 Streamlit 的 session state 中獲取上傳的 PDF 文件
        for source_docs in st.session_state.get('source_docs', []):
            # 創建臨時文件並寫入上傳的內容，確保 delete=False
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tmp_dir.as_posix(), suffix='.pdf') as tmp_file:
                tmp_file.write(source_docs.read())  # 將上傳的 PDF 文件寫入臨時文件

                full_path = tmp_file.name  # 取得臨時文件的完整路徑
                file_name = Path(full_path).name  # 取得臨時文件的名稱
                doc_names[file_name] = source_docs.name  # 記錄原始文件名與臨時文件名的對應關係
                temporary_files.append(full_path)  # 將臨時文件的路徑添加到列表中

                # 日誌紀錄創建的臨時文件路徑
                logging.info(f"Created temporary file: {file_name}")

        # 將檔案名稱對應關係儲存至 Streamlit 的 session state 中
        st.session_state['doc_names'] = doc_names
        print(doc_names)  # 輸出檔案對應關係

        return temporary_files  # 返回創建的臨時文件路徑清單

    def partition_pdf_file(self, file_name):
        """解析 PDF 檔案"""
        # 使用 partition_pdf 函數解析 PDF，根據標題分割內容並推測表格結構
        elements = partition_pdf(
            filename=file_name,
            strategy='hi_res',              # 使用高解析度模式
            hi_res_model_name="yolox",      # 使用 YOLOX 模型來檢測圖像和表格
            extract_images_in_pdf=False,    # 不提取圖像
            infer_table_structure=True,     # 自動推測表格結構
            chunking_strategy="by_title",   # 根據標題分割內容
            max_characters=4000,            # 每個文本區塊的最大字數
            new_after_n_chars=3800,         # 超過 3800 字符時創建新區塊
            combine_text_under_n_chars=2000,                # 將少於 2000 字符的區塊合併
            extract_image_block_output_dir="output_path",   # 圖像區塊的輸出目錄
        )
        return elements  # 返回解析結果

    def summarize_elements(self, elements):
        """對解析出的元素進行摘要生成"""
        text_elements = []      # 儲存文本元素
        table_elements = []     # 儲存表格元素
        text_summaries = []     # 儲存文本摘要
        table_summaries = []    # 儲存表格摘要

        llm = LLMAPI.get_llm()

        # 定義摘要生成的提示模板，根據元素的類型生成摘要
        summary_prompt = """
        Using English to summarize the following {element_type}: 
        {element}
        """
        summary_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(summary_prompt))  # 定義語言模型鏈

        # 迭代每個元素，根據元素類型生成對應的摘要
        for e in elements:
            if 'CompositeElement' in repr(e):  # 如果是文本類型的元素
                text_elements.append(e.text)
                summary = summary_chain.run({'element_type': 'text', 'element': e})  # 生成文本摘要
                text_summaries.append(summary)
            elif 'Table' in repr(e):  # 如果是表格類型的元素
                table_elements.append(e.text)
                summary = summary_chain.run({'element_type': 'table', 'element': e})  # 生成表格摘要
                table_summaries.append(summary)

        return text_elements, table_elements, text_summaries, table_summaries  # 返回摘要結果

    def convert_to_documents(self, text_elements, text_summaries, table_elements, table_summaries):
        """將文本和表格摘要轉換為 Document 物件"""
        documents = []
        retrieve_contents = []

        # 將文本摘要轉換為 Document 並保存
        for e, s in zip(text_elements, text_summaries):
            i = str(uuid.uuid4())  # 生成唯一 ID
            doc = Document(page_content=s,      # 儲存的內容為摘要
                           metadata={
                               'id': i,
                               'type': 'text',
                               'original_content': e    # 保存原始文本
                           }
                           )
            retrieve_contents.append((i, e))
            documents.append(doc)
            print("1", retrieve_contents)
            print("11111111111111", documents)

        # 將表格摘要轉換為 Document 並保存
        for e, s in zip(table_elements, table_summaries):
            i = str(uuid.uuid4())  # 生成唯一ID
            doc = Document(
                page_content=s,  # 儲存的內容為摘要
                metadata={
                    'id': i,
                    'type': 'table',
                    'original_content': e  # 保存原始表格
                }
            )
            retrieve_contents.append((i, e))
            documents.append(doc)
            print("2", retrieve_contents)
            print("222222222222", documents)
            retrieve_contents.append((i, s))
            documents.append(doc)

        return documents  # 返回 Document 集合

    def embeddings_on_local_vectordb(self, documents):
        """將文件塊嵌入本地向量數據庫"""
        if not documents:
            raise ValueError("No document chunks to embed. Please check the text splitting process.")

        # 使用 Chroma 將文件嵌入本地向量庫
        Chroma.from_documents(
            documents,
            embedding=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        logging.info(f"Persisted vector DB at {self.vector_store_dir}")

