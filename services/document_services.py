import streamlit as st
from models.document_model import DocumentModel
from models.database_userRecords import UserRecordsDB
from models.database_devOps import DevOpsDB

class DocumentService:
    def __init__(self):
        # 初始化 DocumentModel
        self.doc_model = DocumentModel()
        self.userRecords_db = UserRecordsDB()
        self.devOps_db = DevOpsDB()

    def process_uploaded_documents(self):
        try:
            """完整的 PDF 處理流程"""
            # 1. 創建臨時文件
            temporary_files = self.doc_model.create_temporary_files()

            # 2. 解析每個臨時 PDF 文件
            for file_name in temporary_files:
                elements = self.doc_model.partition_pdf_file(file_name)

                # 3. 生成文本和表格的摘要
                text_elements, table_elements, text_summaries, table_summaries = self.doc_model.summarize_elements(elements)

                # 4. 將摘要轉換為 Document 物件
                documents = self.doc_model.convert_to_documents(text_elements, text_summaries, table_elements, table_summaries)

                # 5. 將文檔嵌入本地向量庫
                self.doc_model.embeddings_on_local_vectordb(documents)

            self.userRecords_db.save_to_file_names()
            self.devOps_db.save_to_file_names()

            self.userRecords_db.save_to_pdf_uploads()
            self.devOps_db.save_to_pdf_uploads()


        except Exception as e:
            # 處理文檔時發生錯誤，顯示錯誤訊息
            st.error(f"處理文檔時發生錯誤 process_uploaded_documents：{e}")
