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
        loader = PyPDFDirectoryLoader(self.tmp_dir.as_posix(), glob='**/*.pdf')
        documents = loader.load()
        if not documents:
            raise ValueError("No documents loaded. Please check the PDF files.")
        logging.info(f"Loaded {len(documents)} documents")
        return documents

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
