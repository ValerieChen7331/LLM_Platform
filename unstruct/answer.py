# 匯入所需的套件
from unstructured.partition.pdf import partition_pdf
import os
import uuid
import base64
from IPython import display
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.messages import HumanMessage, SystemMessage
from langchain.schema.document import Document
from langchain.vectorstores import FAISS
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
import streamlit as st
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document


# 定義語言模型
def get_llm():
    api_base = 'http://10.5.61.81:11434'  # API 基礎 URL
    model = 'SimonPu/llama-3-taiwan-8b-instruct-dpo'  # 模型名稱
    return Ollama(base_url=api_base, model=model)


# 定義回答問題的函數
def answer(question):
    # 使用 Ollama Embeddings 來處理文本嵌入
    embedding_function = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")

    # 從本地文件加載 FAISS 向量庫
    vectorstore = FAISS.load_local("db", embeddings=embedding_function, allow_dangerous_deserialization=True)

    # 使用向量庫進行相似度搜索，找到與問題相關的文檔
    relevant_docs = vectorstore.similarity_search(question)

    # 構建回答所需的上下文
    context = ""
    for d in relevant_docs:
        # 如果是文本類型的文檔，加入文本上下文
        if d.metadata['type'] == 'text':
            context += '[text]' + d.metadata['original_content']
        # 如果是表格類型的文檔，加入表格上下文
        elif d.metadata['type'] == 'table':
            context += '[table]' + d.metadata['original_content']

    # 使用 LLM Chain 生成回答
    result = answer_chain.run({'context': context, 'question': question})
    return result


# 定義回答模板
answer_template = """
Answer the question based only on the following context, which can include text, images and tables:
{context}
Question: {question} 
"""

# 定義 LLM Chain 來處理回答過程
answer_chain = LLMChain(
    llm=get_llm(),  # 使用語言模型
    prompt=PromptTemplate.from_template(answer_template)  # 使用回答模板
)

# 測試問題回答
result = answer("南亞塑膠工三廠")
print(result)
