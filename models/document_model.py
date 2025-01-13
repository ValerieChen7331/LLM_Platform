import logging
import tempfile
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from apis.file_paths import FilePaths
from apis.embedding_api import EmbeddingAPI
from pathlib import Path
# from langchain_chroma import Chroma
# from langchain.schema.document import Document
# from unstructured.partition.pdf import partition_pdf
# from apis.llm_api import LLMAPI
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain

# 設定日誌記錄的級別為 INFO
logging.basicConfig(level=logging.INFO)

class DocumentModel:
    def __init__(self, chat_session_data):
        # 初始化 hat_session_data
        self.chat_session_data = chat_session_data
        # 初始化文件路徑
        self.file_paths = FilePaths()
        username = self.chat_session_data.get("username")
        conversation_id = self.chat_session_data.get("conversation_id")
        self.tmp_dir = self.file_paths.get_tmp_dir(username, conversation_id)
        self.vector_store_dir = self.file_paths.get_local_vector_store_dir(username, conversation_id)

    def create_temporary_files(self, source_docs):
        """建立臨時文件並返回檔案名稱對應關係。"""
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        doc_names = {}

        for source_doc in source_docs:
            with tempfile.NamedTemporaryFile(delete=False, dir=self.tmp_dir.as_posix(), suffix='.pdf') as tmp_file:
                tmp_file.write(source_doc['content'])  # 寫入文件內容
                file_name = Path(tmp_file.name).name
                doc_names[file_name] = source_doc['name']
                logging.info(f"Created temporary file: {file_name}")

        return doc_names

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

    def delete_temporary_files(self):
        # 刪除臨時文件
        for file in self.tmp_dir.iterdir():
            try:
                logging.info(f"Deleting temporary file: {file}")
                file.unlink()
            except Exception as e:
                logging.error(f"Error deleting file {file}: {e}")

    def split_documents_into_chunks(self, documents):
        print(documents)
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
        mode = self.chat_session_data.get("mode")
        embedding = self.chat_session_data.get("embedding")
        embedding_function = EmbeddingAPI.get_embedding_function(mode, embedding)
        if not document_chunks:
            raise ValueError("No document chunks to embed. Please check the text splitting process.")

        Chroma.from_documents(
            document_chunks,
            embedding=embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        logging.info(f"Persisted vector DB at {self.vector_store_dir}")
