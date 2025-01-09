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
from langchain_community.vectorstores import Chroma

# 定義輸出圖像的路徑
output_path = "image"
# 定義PDF檔案的名稱
fname = "test.pdf"

# 解析PDF檔案
elements = partition_pdf(
    filename=fname,
    strategy='hi_res',  # 使用高解析度模式
    hi_res_model_name="yolox",  # 使用YOLOX模型
    extract_images_in_pdf=False,  # 不提取PDF中的圖像
    infer_table_structure=True,  # 自動推測表格結構
    chunking_strategy="by_title",  # 依據標題分割內容
    max_characters=4000,  # 每個區塊的最大字數
    new_after_n_chars=3800,  # 當字數超過3800時創建新區塊
    combine_text_under_n_chars=2000,  # 將字數少於2000的區塊合併
    extract_image_block_output_dir=output_path,  # 圖像區塊的輸出目錄
)

# 定義語言模型
def get_llm():
    api_base = 'http://10.5.61.81:11434'  # API基礎URL
    model = 'SimonPu/llama-3-taiwan-8b-instruct-dpo'  # 模型名稱
    return Ollama(base_url=api_base, model=model)

# 初始化變數
text_elements = []  # 儲存文本元素
table_elements = []  # 儲存表格元素
text_summaries = []  # 儲存文本摘要
table_summaries = []  # 儲存表格摘要

# 定義摘要提示模板
summary_prompt = """
Using English to summarize the following {element_type}: 
{element}
"""

# 定義摘要生成鏈
summary_chain = LLMChain(
    llm=get_llm(),  # 使用的語言模型
    prompt=PromptTemplate.from_template(summary_prompt)  # 使用的提示模板
)

# 解析PDF中的每個元素，並根據元素類型生成摘要
for e in elements:
    print(repr(e))
    if 'CompositeElement' in repr(e):  # 如果是文本類型的元素
        text_elements.append(e.text)
        summary = summary_chain.run({'element_type': 'text', 'element': e})  # 生成文本摘要
        text_summaries.append(summary)
    elif 'Table' in repr(e):  # 如果是表格類型的元素
        table_elements.append(e.text)
        summary = summary_chain.run({'element_type': 'table', 'element': e})  # 生成表格摘要
        table_summaries.append(summary)

# 打印結果
print(table_elements)
print(text_elements)
print(text_summaries)
print(table_summaries)

# 匯入所需的Embedding模組
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document

# 初始化變數
documents = []
retrieve_contents = []

# 將文本摘要轉換為Document並加入文件集合
for e, s in zip(text_elements, text_summaries):
    i = str(uuid.uuid4())  # 生成唯一ID
    doc = Document(
        page_content=s,  # 儲存的內容為摘要
        metadata={
            'id': i,
            'type': 'text',
            'original_content': e  # 保存原始文本
        }
    )
    retrieve_contents.append((i, e))  # 儲存ID和原始內容
    documents.append(doc)  # 將Document加入集合
    print("1", retrieve_contents)
    print("11111111111111", documents)

# 將表格摘要轉換為Document並加入文件集合
for e, s in zip(table_elements, table_summaries):
    i = str(uuid.uuid4())  # 生成唯一ID
    doc = Document(
        page_content=s,  # 儲存的內容為摘要
        metadata={
            'id': i,
            'type': 'table',
            'original_content': e  # 保存原始表格
        }
    )
    retrieve_contents.append((i, e))  # 儲存ID和原始內容
    documents.append(doc)  # 將Document加入集合
    print("2", retrieve_contents)
    print("222222222222", documents)
    retrieve_contents.append((i, s))  # 再次儲存ID和摘要
    documents.append(doc)

# 使用OllamaEmbeddings生成向量
embedding_function = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")

# 使用 Chroma 構建向量庫並將文件加入
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embedding_function,
    persist_directory="db"  # 在初始化時指定保存目錄
)


