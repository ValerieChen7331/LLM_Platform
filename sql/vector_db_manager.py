from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from sql.db_connection import db_connection
from sql.llm import llm
import ast
import re
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
VECTOR_DB_PATH = "sql/sql/vector_db.faiss"

def save_vector_db(vector_db):
    """保存向量資料庫到檔案"""
    vector_db.save_local(VECTOR_DB_PATH)

def load_vector_db():
    """從檔案中載入向量資料庫"""
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(VECTOR_DB_PATH, OllamaEmbeddings(base_url="http://10.5.61.81:11433", model="bge-m3"),allow_dangerous_deserialization=True)
    return None

def create_vector_db_from_texts(texts):
    """從文本生成向量資料庫"""
    embeddings = OllamaEmbeddings(base_url="http://10.5.61.81:11433", model="bge-m3")
    
    vector_db = FAISS.from_texts(texts, embeddings)
    print("emb finish")
    save_vector_db(vector_db)
    return vector_db

def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    return list(set(res))

def initialize_and_save_vector_db(db_name, db_source):
    db = db_connection(db_name, db_source)
    # YM = query_as_list(db, "SELECT YM FROM CC17")
    # CO = query_as_list(db, "SELECT CO FROM CC17")
    # DIV = query_as_list(db, "SELECT DIV FROM CC17")
    # PLD = query_as_list(db, "SELECT PLD FROM CC17")
    # DP = query_as_list(db, "SELECT DP FROM CC17")
    ACCT = query_as_list(db, "SELECT ACCT FROM CC17")
    EGNO = query_as_list(db, "SELECT EGNO FROM CC17")
    # EGNM = query_as_list(db, "SELECT EGNM FROM CC17")
    # URID = query_as_list(db, "SELECT URID FROM CC17")
    # MTNO = query_as_list(db, "SELECT MTNO FROM CC17")
    # MTNM = query_as_list(db, "SELECT MTNM FROM CC17")
    # SUMR = query_as_list(db, "SELECT SUMR FROM CC17")
    # QTY = query_as_list(db, "SELECT QTY FROM CC17")
    # AMT = query_as_list(db, "SELECT AMT FROM CC17")
    # PURURCOMT = query_as_list(db, "SELECT PURURCOMT FROM CC17")
    VOCHCSUMR = query_as_list(db, "SELECT VOCHCSUMR FROM CC17")
    # FBEN = query_as_list(db, "SELECT FBEN FROM CC17")
    # USSHNO = query_as_list(db, "SELECT USSHNO FROM CC17")
    VOCHNO = query_as_list(db, "SELECT VOCHNO FROM CC17")
    # IADAT = query_as_list(db, "SELECT IADAT FROM CC17")
    PVNO = query_as_list(db, "SELECT PVNO FROM CC17")
    # SALID = query_as_list(db, "SELECT SALID FROM CC17")
    # JBDP = query_as_list(db, "SELECT JBDP FROM CC17")
    # IT = query_as_list(db, "SELECT IT FROM CC17")
    print("emb")
    vector_db = create_vector_db_from_texts(ACCT+EGNO+VOCHCSUMR+VOCHNO+PVNO)
    print("Vector database successfully created and saved to", VECTOR_DB_PATH)

if __name__ == "__main__":
    # 提供資料庫名稱和來源，這些參數應該根據你的實際情況來設置
    db_name = "CC17"
    db_source = "SQLITE"
    
    initialize_and_save_vector_db(db_name, db_source)



# 輸出結果

