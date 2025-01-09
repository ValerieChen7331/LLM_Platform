from unstructured.partition.pdf import partition_pdf
import os
import uuid
import base64
from IPython import display
from unstructured.partition.pdf import partition_pdf
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

def get_llm():
    api_base = 'http://10.5.61.81:11434'
    model = 'SimonPu/llama-3-taiwan-8b-instruct-dpo'
    return Ollama(base_url=api_base, model=model)
def answer(question):
    embedding_function = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")
    vectorstore = FAISS.load_local("db", embeddings=embedding_function, allow_dangerous_deserialization=True)
    # 使用加載的 vectorstore 進行相似度搜索
    relevant_docs = vectorstore.similarity_search(question)
    
    # 其餘邏輯和之前相同
    context = ""
    for d in relevant_docs:
        if d.metadata['type'] == 'text':
            context += '[text]' + d.metadata['original_content']
        elif d.metadata['type'] == 'table':
            context += '[table]' + d.metadata['original_content']
    result = answer_chain.run({'context': context, 'question': question})
    return result

answer_template = """
Answer the question based only on the following context, which can include text, images and tables:
{context}
Question: {question} 
"""
answer_chain = LLMChain(
    llm=get_llm(),
    prompt=PromptTemplate.from_template(answer_template)
)
result = answer("南亞塑膠工三廠")
print(result)


