import streamlit as st
from models.document_model import DocumentModel

class DocumentService:
    def __init__(self):
        # 初始化 DocumentModel
        self.doc_model = DocumentModel()

    def process_uploaded_documents(self):
        try:
            # 建立臨時文件
            self.doc_model.create_temporary_files()
            # 加載文檔
            documents = self.doc_model.load_documents()
            # 刪除臨時文件
            self.doc_model.delete_temporary_files()
            # 將文檔拆分成塊
            document_chunks = self.doc_model.split_documents_into_chunks(documents)
            # 在本地向量數據庫中嵌入文檔塊
            st.session_state['retriever'] = self.doc_model.embeddings_on_local_vectordb(document_chunks)

        except Exception as e:
            # 處理文檔時發生錯誤，顯示錯誤訊息
            st.error(f"處理文檔時發生錯誤：{e}")
