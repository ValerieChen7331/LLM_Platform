import logging
import tempfile
import streamlit as st
from pathlib import Path
import json

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

from langchain.schema.document import Document
from apis.file_paths import FilePaths
from apis.embedding_api import EmbeddingAPI

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
        # 建立臨時文件
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        temporary_files = []
        for source_docs in st.session_state.get('source_docs', []):
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tmp_dir.as_posix(), suffix='.pdf') as tmp_file:
                tmp_file.write(source_docs.read())
                temporary_files.append(tmp_file.name)
                logging.info(f"Created temporary file: {tmp_file.name}")
            tmp_file.close()
        return temporary_files

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
            chunk_size=200,
            chunk_overlap=100,
            length_function=len
        )
        document_chunks = text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(document_chunks)} chunks")
        return document_chunks

    def embeddings_on_local_vectordb(self, document_chunks):
        # 將文檔塊嵌入本地向量數據庫，並返回檢索器設定
        if not document_chunks:
            raise ValueError("No document chunks to embed. Please check the text splitting process.")

        vector_db = Chroma.from_documents(
            document_chunks,
            embedding=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        logging.info(f"Persisted vector DB at {self.vector_store_dir}")

        #retriever = vector_db.as_retriever(search_kwargs={'k': 3})

        #st.session_state['retriever'] = retriever

        # 指定要保存 JSON 文件的路徑和名稱
        #retriever_json = retriever.to_json()
        #json_file_path = Path(self.vector_store_dir) / "retriever_config.json"

        # 將 retriever_json 保存為 JSON 文件
        #with open(json_file_path, 'w') as json_file:
        #    json.dump(retriever_json, json_file, indent=4)

        #logging.info(f"Retriever JSON configuration saved at {json_file_path}")
        #print(retriever_json)
        #return retriever

    def load_retriever_from_json(self):
        # 指定要讀取的 JSON 文件的路徑和名稱
        json_file_path = Path(self.vector_store_dir) / "retriever_config.json"

        if not json_file_path.exists():
            raise FileNotFoundError(f"JSON configuration file not found at {json_file_path}")

        # 從 JSON 文件中讀取 retriever 的設定
        with open(json_file_path, 'r') as json_file:
            retriever_json = json.load(json_file)

        # 使用 Chroma 類來創建 retriever 對象
        vector_db = Chroma(
            embedding=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )

        # 設置 retriever 的參數，這里直接使用 JSON 中的設置
        retriever = vector_db.as_retriever(search_kwargs=retriever_json.get("search_kwargs", {'k': 3}))

        # 將 retriever 保存到 session state
        st.session_state['retriever'] = retriever

        logging.info(f"Retriever loaded from JSON configuration at {json_file_path}")
        return retriever
