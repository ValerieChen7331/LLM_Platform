import streamlit as st
from models.document_model import DocumentModel
from models.database_userRecords import UserRecordsDB
from models.database_devOps import DevOpsDB

class DocumentService:
    def __init__(self, chat_session_data):
        # 初始化 DocumentModel
        self.doc_model = DocumentModel(chat_session_data)
        self.userRecords_db = UserRecordsDB(chat_session_data)
        self.devOps_db = DevOpsDB(chat_session_data)

    def process_uploaded_documents(self, chat_session_data, source_docs):
        try:
            # 建立臨時文件
            doc_names = self.doc_model.create_temporary_files(source_docs)
            chat_session_data['doc_names'] = doc_names

            # 加載文檔
            documents = self.doc_model.load_documents()

            # 刪除臨時文件
            #self.doc_model.delete_temporary_files()

            # 將文檔拆分成塊
            document_chunks = self.doc_model.split_documents_into_chunks(documents)

            # 在本地向量數據庫中嵌入文檔塊
            self.doc_model.embeddings_on_local_vectordb(document_chunks)

            self.userRecords_db.save_to_file_names()
            self.devOps_db.save_to_file_names()

            self.userRecords_db.save_to_pdf_uploads()
            self.devOps_db.save_to_pdf_uploads()

            return chat_session_data

        except Exception as e:
            # 處理文檔時發生錯誤，顯示錯誤訊息
            st.error(f"處理文檔時發生錯誤 process_uploaded_documents：{e}")
