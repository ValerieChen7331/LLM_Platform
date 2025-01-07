import streamlit as st
from models.document_model import DocumentModel

class DocumentService:
    def __init__(self):
        self.doc_model = DocumentModel()

    def process_uploaded_documents(self):
        if not self.doc_model.validate_api_credentials():
            st.warning("請提供 LLM 模型 API 訊息。")
            return

        try:
            self.doc_model.create_temporary_files()
            documents = self.doc_model.load_documents()
            self.doc_model.delete_temporary_files()
            document_chunks = self.doc_model.split_documents_into_chunks(documents)
            st.session_state['retriever'] = self.doc_model.embeddings_on_local_vectordb(document_chunks)
        except Exception as e:
            st.error(f"處理文檔時發生錯誤：{e}")