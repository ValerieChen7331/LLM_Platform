import logging
import tempfile
import streamlit as st
from pathlib import Path
import pandas as pd
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema.document import Document
from apis.file_paths import FilePaths
from apis.embedding_api import EmbeddingAPI

logging.basicConfig(level=logging.INFO)

class DocumentModel:
    def __init__(self):
        self.file_paths = FilePaths()
        self.tmp_dir, self.vector_store_dir, self.output_dir = self.file_paths.get_doc_paths()
        self.embedding_function = EmbeddingAPI.get_embedding_function("http://10.5.61.81:11435", "llama3")

    def validate_api_credentials(self):
        api_base = st.session_state.get('api_base', None)
        api_key = st.session_state.get('api_key', None)
        return api_base and api_key

    def create_temporary_files(self):
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
        loader = PyPDFDirectoryLoader(self.tmp_dir.as_posix(), glob='**/*.pdf')
        documents = loader.load()
        if not documents:
            raise ValueError("No documents loaded. Please check the PDF files.")
        logging.info(f"Loaded {len(documents)} documents")
        return documents

    def delete_temporary_files(self):
        for file in self.tmp_dir.iterdir():
            try:
                logging.info(f"Deleting temporary file: {file}")
                file.unlink()
            except Exception as e:
                logging.error(f"Error deleting file {file}: {e}")

    def split_documents_into_chunks(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=200,
            length_function=len
        )
        document_chunks = text_splitter.split_documents(documents)
        logging.info(f"Split documents into {len(document_chunks)} chunks")
        return document_chunks

    def embeddings_on_local_vectordb(self, document_chunks):
        if not document_chunks:
            raise ValueError("No document chunks to embed. Please check the text splitting process.")
        vector_db = Chroma.from_documents(
            document_chunks,
            embedding=self.embedding_function,
            persist_directory=self.vector_store_dir.as_posix()
        )
        logging.info(f"Persisted vector DB at {self.vector_store_dir}")
        retriever = vector_db.as_retriever(search_kwargs={'k': 3})
        return retriever
