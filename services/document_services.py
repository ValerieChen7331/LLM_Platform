import streamlit as st
from models.document_model import DocumentModel
from models.batabase_userRecords import UserRecordsDB
from models.batabase_devOps import DevOpsDB

class DocumentService:
    def __init__(self):
        # 初始化 DocumentModel
        self.doc_model = DocumentModel()
        self.userRecords_db = UserRecordsDB()
        self.devOps_db = DevOpsDB()

    def process_uploaded_documents(self):
        try:
            # 建立臨時文件
            self.doc_model.create_temporary_files()
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


        except Exception as e:
            # 處理文檔時發生錯誤，顯示錯誤訊息
            st.error(f"處理文檔時發生錯誤 process_uploaded_documents：{e}")
