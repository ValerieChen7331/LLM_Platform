import logging
import tempfile
import streamlit as st

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
# from langchain_chroma import Chroma
from langchain.schema.document import Document
from apis.file_paths import FilePaths
from apis.embedding_api import EmbeddingAPI
from pathlib import Path

from unstructured.partition.pdf import partition_pdf
from apis.llm_api import LLMAPI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain



# 設定日誌記錄的級別為 INFO
logging.basicConfig(level=logging.INFO)


class DocumentModel:
    def __init__(self):
        # 初始化文件路徑和嵌入函數
        self.file_paths = FilePaths()
        self.tmp_dir = self.file_paths.get_tmp_dir()
        self.vector_store_dir = self.file_paths.get_local_vector_store_dir()
        self.embedding_function = EmbeddingAPI.get_embedding_function()

    def create_temporary_files(self):
        """建立臨時文件"""
        # 確保臨時目錄已存在，如果不存在則創建該目錄
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        temporary_files = []        # 用來儲存臨時文件的文件清單
        doc_names = {}              # 用來儲存原始文件名與臨時文件名的對應關係

        # 從 Streamlit 的 session state 中獲取 'source_docs' 列表，如果沒有就使用空列表
        for source_docs in st.session_state.get('source_docs', []):
            # 指定臨時文件的目錄為 self.tmp_dir，文件後綴為 '.pdf'。設定 delete=False 以確保文件不會在關閉時被自動刪除
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tmp_dir.as_posix(), suffix='.pdf') as tmp_file:
                # 將 source_docs 的內容寫入臨時文件中
                tmp_file.write(source_docs.read())

                # 取得臨時文件的完整路徑
                full_path = tmp_file.name
                # 使用 Path 對象取得檔案名稱（不包括路徑）
                file_name = Path(full_path).name
                # 將原始文件名和臨時文件名加入字典
                doc_names[file_name] = source_docs.name

                # 將創建的臨時文件名添加到 temporary_files 列表中
                #temporary_files.append(tmp_file.name)

                # 記錄一條信息日誌，顯示創建的臨時文件的路徑
                logging.info(f"Created temporary file: {file_name}")

            # 關閉臨時文件（這行其實可以省略，因為 with 語句會自動關閉文件）
            tmp_file.close()

        # 將檔案名稱對應關係儲存到 session state 中
        st.session_state['doc_names'] = doc_names
        print(doc_names)

    def load_documents(self):
        # 加載 PDF 文件
        # 使用 PyPDFDirectoryLoader 從指定的目錄中加載所有 PDF 文件
        loader = PyPDFDirectoryLoader(self.tmp_dir.as_posix(), glob='**/*.pdf')

        # 加載 PDF 文件，並將其儲存在 documents 變數中
        documents = loader.load()

        # 如果沒有加載到任何文件，拋出異常提示
        if not documents:
            raise ValueError("No documents loaded. Please check the PDF files.")

        # 紀錄已加載的文件數量到日誌中
        logging.info(f"Loaded {len(documents)} documents")

        # 返回已加載的文件
        return documents

    def create_partition_pdf(self):
        """建立臨時文件並解析PDF檔案"""
        # 確保臨時目錄已存在，如果不存在則創建該目錄
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        temporary_files = []  # 用來儲存臨時文件的文件清單
        doc_names = {}  # 用來儲存原始文件名與臨時文件名的對應關係

        # 從 Streamlit 的 session state 中獲取 'source_docs' 列表，如果沒有就使用空列表
        for source_docs in st.session_state.get('source_docs', []):
            # 指定臨時文件的目錄為 self.tmp_dir，文件後綴為 '.pdf'，設定 delete=False 以確保文件不會在關閉時被自動刪除
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tmp_dir.as_posix(), suffix='.pdf') as tmp_file:
                # 將 source_docs 的內容寫入臨時文件中
                tmp_file.write(source_docs.read())

                # 取得臨時文件的完整路徑
                full_path = tmp_file.name
                # 使用 Path 對象取得檔案名稱（不包括路徑）
                file_name = Path(full_path).name
                # 將原始文件名和臨時文件名加入字典
                doc_names[file_name] = source_docs.name

                # 將創建的臨時文件路徑加入 temporary_files 列表
                temporary_files.append(full_path)

                # 記錄一條信息日誌，顯示創建的臨時文件的路徑
                logging.info(f"Created temporary file: {file_name}")

            # 自動關閉臨時文件
            tmp_file.close()

        # 將檔案名稱對應關係儲存到 session state 中
        st.session_state['doc_names'] = doc_names
        print(doc_names)

        # 解析每個臨時文件的 PDF
        for file_name in temporary_files:
            elements = partition_pdf(
                filename=file_name,
                strategy='hi_res',  # 使用高解析度模式
                hi_res_model_name="yolox",  # 使用YOLOX模型
                extract_images_in_pdf=False,  # 不提取PDF中的圖像
                infer_table_structure=True,  # 自動推測表格結構
                chunking_strategy="by_title",  # 依據標題分割內容
                max_characters=4000,  # 每個區塊的最大字數
                new_after_n_chars=3800,  # 當字數超過3800時創建新區塊
                combine_text_under_n_chars=2000,  # 將字數少於2000的區塊合併
                extract_image_block_output_dir="output_path",  # 圖像區塊的輸出目錄
            )
            # 打印每個 PDF 解析結果
            print(elements)

            # 初始化變數
            text_elements = []  # 儲存文本元素
            table_elements = []  # 儲存表格元素
            text_summaries = []  # 儲存文本摘要
            table_summaries = []  # 儲存表格摘要

            # 定義摘要提示模板
            summary_prompt = """
            Using English to summarize the following {element_type}: 
            {element}
            """

            # 定義摘要生成鏈
            summary_chain = LLMChain(
                llm=LLMAPI.get_llm(),  # 使用的語言模型
                prompt=PromptTemplate.from_template(summary_prompt)  # 使用的提示模板
            )

            # 解析PDF中的每個元素，並根據元素類型生成摘要
            for e in elements:
                print(repr(e))
                if 'CompositeElement' in repr(e):  # 如果是文本類型的元素
                    text_elements.append(e.text)
                    summary = summary_chain.run({'element_type': 'text', 'element': e})  # 生成文本摘要
                    text_summaries.append(summary)
                elif 'Table' in repr(e):  # 如果是表格類型的元素
                    table_elements.append(e.text)
                    summary = summary_chain.run({'element_type': 'table', 'element': e})  # 生成表格摘要
                    table_summaries.append(summary)

            # 打印結果
            print(table_elements)
            print(text_elements)
            print(text_summaries)
            print(table_summaries)

            # 匯入所需的Embedding模組
            from langchain_community.embeddings import OllamaEmbeddings
            from langchain.schema import Document

            # 初始化變數
            documents = []
            retrieve_contents = []

            # 將文本摘要轉換為Document並加入文件集合
            for e, s in zip(text_elements, text_summaries):
                i = str(uuid.uuid4())  # 生成唯一ID
                doc = Document(
                    page_content=s,  # 儲存的內容為摘要
                    metadata={
                        'id': i,
                        'type': 'text',
                        'original_content': e  # 保存原始文本
                    }
                )
                retrieve_contents.append((i, e))  # 儲存ID和原始內容
                documents.append(doc)  # 將Document加入集合
                print("1", retrieve_contents)
                print("11111111111111", documents)

            # 將表格摘要轉換為Document並加入文件集合
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
                retrieve_contents.append((i, e))  # 儲存ID和原始內容
                documents.append(doc)  # 將Document加入集合
                print("2", retrieve_contents)
                print("222222222222", documents)
                retrieve_contents.append((i, s))  # 再次儲存ID和摘要
                documents.append(doc)


    def delete_temporary_files(self):
        # 刪除臨時文件
        for file in self.tmp_dir.iterdir():
            try:
                logging.info(f"Deleting temporary file: {file}")
                file.unlink()
            except Exception as e:
                logging.error(f"Error deleting file {file}: {e}")

    def split_documents_into_chunks(self, documents):
        # 將文件拆分成塊
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=200,
            length_function=len
        )
        document_chunks = text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(document_chunks)} chunks")
        return document_chunks

    def embeddings_on_local_vectordb(self, document_chunks):
        # 將文檔塊嵌入本地向量數據庫，並返回檢索器設定
        if not document_chunks:
            raise ValueError("No document chunks to embed. Please check the text splitting process.")

        Chroma.from_documents(
            document_chunks,
            embedding=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        logging.info(f"Persisted vector DB at {self.vector_store_dir}")
