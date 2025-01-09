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

output_path="image"
fname = "test7.pdf"
elements = partition_pdf(filename=fname,
                         strategy='hi_res',
                         hi_res_model_name="yolox",
                         extract_images_in_pdf=False,
                         infer_table_structure=True,
                         chunking_strategy="by_title",
                         max_characters=4000,
                         new_after_n_chars=3800,
                         combine_text_under_n_chars=2000,
                         extract_image_block_output_dir=output_path,
           )
def get_llm():
    api_base = 'http://10.5.61.81:11434'
    model = 'SimonPu/llama-3-taiwan-8b-instruct-dpo'
    return Ollama(base_url=api_base, model=model)


import os
import uuid
import base64
text_elements = []
table_elements = []

text_summaries = []
table_summaries = []

summary_prompt = """
Using English to summarize the following {element_type}: 
{element}
"""
summary_chain = LLMChain(
    llm=get_llm(),
    prompt=PromptTemplate.from_template(summary_prompt)
)
for e in elements:
    print(repr(e))
    if 'CompositeElement' in repr(e):
        text_elements.append(e.text)
        summary = summary_chain.run({'element_type': 'text', 'element': e})
        text_summaries.append(summary)
    elif 'Table' in repr(e):
        table_elements.append(e.text)
        summary = summary_chain.run({'element_type': 'table', 'element': e})
        table_summaries.append(summary)


print(table_elements)
print(text_elements)
print(text_summaries)
print(table_summaries)


from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema import Document
documents = []
retrieve_contents = []

for e, s in zip(text_elements, text_summaries):
    i = str(uuid.uuid4())
    doc = Document(
        page_content = s,
        metadata = {
            'id': i,
            'type': 'text',
            'original_content': e
        }
    )
    retrieve_contents.append((i, e))
    documents.append(doc)
    print("1",retrieve_contents)
    print("11111111111111",documents)
    
for e, s in zip(table_elements, table_summaries):
    i = str(uuid.uuid4())
    doc = Document(
        page_content = s,
        metadata = {
            'id': i,
            'type': 'table',
            'original_content': e
        }
    )
    retrieve_contents.append((i, e))
    documents.append(doc)
    print("2",retrieve_contents)
    print("222222222222",documents)
    retrieve_contents.append((i, s))
    documents.append(doc)
embedding_function = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")
vectorstore = FAISS.from_documents(documents=documents, embedding=embedding_function)
# 保存 vectorstore 到本地文件
vectorstore.save_local("db")


