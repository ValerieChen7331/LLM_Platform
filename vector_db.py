import logging
import tempfile
import streamlit as st
from pathlib import Path
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from apis.embedding_api import EmbeddingAPI

# 設定日誌記錄的級別為 INFO
logging.basicConfig(level=logging.INFO)

# 設定基礎目錄路徑
base_dir = Path(__file__).resolve().parent.parent.joinpath('data')

# 從 session state 獲取使用者名稱和會話 ID
username = st.session_state.get('username')
conversation_id = st.session_state.get('conversation_id')

# 設定目錄路徑
TMP_DIR = base_dir.joinpath(f"user/{username}/tmp")
LOCAL_VECTOR_STORE_DIR = base_dir.joinpath(f"user/{username}/vector_store/{conversation_id}")
User_Records_DIR = base_dir.joinpath('user')

# 設定嵌入函數
embedding_function = EmbeddingAPI.get_embedding_function()

def create_temporary_files():
    """建立臨時文件。"""
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    temporary_files = []
    for source_docs in st.session_state.get('source_docs', []):
        with tempfile.NamedTemporaryFile(delete=False, dir=TMP_DIR.as_posix(), suffix='.pdf') as tmp_file:
            tmp_file.write(source_docs.read())
            temporary_files.append(tmp_file.name)
            logging.info(f"Created temporary file: {tmp_file.name}")
        tmp_file.close()
    return temporary_files

def load_documents():
    """加載 PDF 文件。"""
    loader = PyPDFDirectoryLoader(TMP_DIR.as_posix(), glob='**/*.pdf')
    documents = loader.load()
    if not documents:
        raise ValueError("No documents loaded. Please check the PDF files.")
    logging.info(f"Loaded {len(documents)} documents")
    return documents

def delete_temporary_files():
    """刪除臨時文件。"""
    for file in TMP_DIR.iterdir():
        try:
            logging.info(f"Deleting temporary file: {file}")
            file.unlink()
        except Exception as e:
            logging.error(f"Error deleting file {file}: {e}")

def split_documents_into_chunks(documents):
    """將文件拆分成塊。"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=200,
        length_function=len
    )
    document_chunks = text_splitter.split_documents(documents)
    logging.info(f"Split documents into {len(document_chunks)} chunks")
    return document_chunks

def embeddings_on_local_vectordb(document_chunks):
    """將文檔塊嵌入本地向量數據庫，並返回檢索器設定。"""
    if not document_chunks:
        raise ValueError("No document chunks to embed. Please check the text splitting process.")

    vector_db = Chroma.from_documents(
        document_chunks,
        embedding=embedding_function,
        persist_directory=LOCAL_VECTOR_STORE_DIR.as_posix()
    )
    logging.info(f"Persisted vector DB at {LOCAL_VECTOR_STORE_DIR}")

def init_vectordb():
    """初始化向量數據庫。"""
    vector_db = Chroma(
        embedding=embedding_function,
        persist_directory=LOCAL_VECTOR_STORE_DIR.as_posix()
    )

    logging.info(f"init_vectordb at {LOCAL_VECTOR_STORE_DIR}")

def query_llm_rag(query):
    """使用 RAG 查詢 LLM，根據給定的問題和檢索的文件內容返回答案。"""
    try:
        vector_db = Chroma(
            embedding_function=embedding_function,
            persist_directory=LOCAL_VECTOR_STORE_DIR.as_posix()
        )
        retriever = vector_db.as_retriever(search_kwargs={'k': 3})
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=LLMAPI.get_llm(),
            retriever=retriever,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": _rag_prompt()}
        )

        chat_history = []  # 初始化聊天歷史記錄
        result_rag = qa_chain.invoke({'question': query, 'chat_history': chat_history})

        response = result_rag.get('answer', '')
        retrieved_documents = result_rag.get('source_documents', [])

        return response, retrieved_documents

    except Exception as e:
        return print(f"查詢 query_llm_rag 時發生錯誤: {e}"), []

def _rag_prompt():
    """生成 RAG 查詢 LLM 所需的提示模板。"""
    template = """
        請根據「文件內容」回答問題。如果以下資訊不足，請如實告知，勿自行編造!
        歷史紀錄越下面是越新的，若需參考歷史紀錄，請以較新的問答為優先。
        若無特別說明，請使用繁體中文來回答問題：
        問答歷史紀錄: {chat_history}
        文件內容: {context}
        問題: {question}
        答案:
    """
    return PromptTemplate(input_variables=["chat_history", "context", "question"], template=template)
