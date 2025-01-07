import os
import tempfile
import sqlite3
from pathlib import Path
import uuid

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

TMP_DIR = Path(__file__).resolve().parent.joinpath('data', 'tmp')
LOCAL_VECTOR_STORE_DIR = Path(__file__).resolve().parent.joinpath('data', 'vector_store')
DATABASE = Path(__file__).resolve().parent.joinpath('data', 'chat_history.db')

st.set_page_config(page_title="南亞塑膠生成式AI")

with open('login_config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

def login_page():
    authenticator.login(fields={'Form name':'Login', 'Username':'Username', 'Password':'Password'})

def main_page():
    st.title("南亞塑膠生成式AI")

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = {
            '內部LLM': {},
            '外部LLM': {}
        }
        load_chat_history()

    if 'current_chat_index' not in st.session_state:
        st.session_state['current_chat_index'] = 0

    if 'mode' not in st.session_state:
        st.session_state['mode'] = '內部LLM'

    if 'current_model' not in st.session_state:
        st.session_state['current_model'] = None

    if 'conversation_id' not in st.session_state:
        st.session_state['conversation_id'] = str(uuid.uuid4())

    with st.sidebar:
        user_name = st.session_state["username"]
        st.write('Welcome ' + user_name)
        if st.button("new chat"):
            current_model = st.session_state.get('current_model', '')
            st.session_state['conversation_id'] = str(uuid.uuid4())
            if current_model:
                if current_model not in st.session_state['chat_history'][st.session_state['mode']]:
                    st.session_state['chat_history'][st.session_state['mode']][current_model] = []
                st.session_state['chat_history'][st.session_state['mode']][current_model].append([])
                st.session_state['current_chat_index'] = len(st.session_state['chat_history'][st.session_state['mode']][current_model]) - 1
        
        st.title("選項")
        
        new_mode = st.radio("LLM 類型：", ('內部LLM', '外部LLM'))
        if new_mode != st.session_state['mode']:
            st.session_state['mode'] = new_mode
            st.session_state['current_model'] = None
            st.session_state['current_chat_index'] = 0
            st.session_state['conversation_id'] = str(uuid.uuid4())

        if st.session_state['mode'] == '內部LLM':
            options = ["qwen2:7b", "SimonPu/llama-3-taiwan-8b-instruct-dpo", "wangrongsheng/taiwanllm-13b-v2.0-chat", "wangshenzhi/gemma2-9b-chinese-chat"]
            model = st.selectbox('選擇一個選項:', options, key='model_select')
            openai_api_base = 'http://10.5.61.81:11434'
            openai_api_key = 'None'
        elif st.session_state['mode'] == '外部LLM':
            model = st.text_input('輸入模型名稱:', key='model_input')
            openai_api_base = st.text_input('API Base:', type='password')
            openai_api_key = st.text_input('API Key:', type='password')

        if model and model != st.session_state['current_model']:
            st.session_state['current_model'] = model
            st.session_state['current_chat_index'] = 0
            st.session_state['conversation_id'] = str(uuid.uuid4())
            if model not in st.session_state['chat_history'][st.session_state['mode']]:
                st.session_state['chat_history'][st.session_state['mode']][model] = [[]]

        st.title("聊天記錄")
        current_model = st.session_state.get('current_model', '')
        if current_model in st.session_state['chat_history'][st.session_state['mode']]:
            chats = st.session_state['chat_history'][st.session_state['mode']][current_model]
            if chats:
                for i, chat in enumerate(chats):
                    if chat:
                        title = chat[0][0] if chat else f"對話 {i+1}"
                        col1, col2 = st.columns([4, 1])
                        if col1.button(title, key=f'chat_select_{i}'):
                            st.session_state['current_chat_index'] = i
                        if col2.button("X", key=f'delete_{i}'):
                            delete_chat_history_and_update_indexes(st.session_state['mode'], current_model, i)
                            st.experimental_rerun()
            else:
                st.session_state['current_chat_index'] = 0
        else:
            st.session_state['current_chat_index'] = 0
            
    st.markdown(f"""
    <style>
        div.stButton > button {{
            background-color: transparent;
            border: strict;
            border-radius: 5px;
            font-weight: bold;
            margin: -5px 0;
            padding: 10px 20px;
            width: 100%;
            display: flex;
            justify-content: flex-start;
            align-items: center;
        }}
        div.stButton > button:hover {{
            background-color: #e0e0e0;
        }}
    </style>
    """, unsafe_allow_html=True)

    return model, openai_api_base, openai_api_key

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY, conversation_id TEXT, mode TEXT, model TEXT, chat_index INTEGER, user_query TEXT, ai_response TEXT, summary TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pdf_uploads
                 (id INTEGER PRIMARY KEY, pdf_path TEXT, embeddings_path TEXT, upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def execute_query(query, params=()):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_query(query, params=()):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return results

def load_chat_history():
    chat_history = fetch_query("SELECT conversation_id, mode, model, chat_index, user_query, ai_response, summary FROM chat_history")
    for conversation_id, mode, model, chat_index, user_query, ai_response, summary in chat_history:
        if mode not in st.session_state['chat_history']:
            st.session_state['chat_history'][mode] = {}
        if model not in st.session_state['chat_history'][mode]:
            st.session_state['chat_history'][mode][model] = []
        while len(st.session_state['chat_history'][mode][model]) <= chat_index:
            st.session_state['chat_history'][mode][model].append([])
        st.session_state['chat_history'][mode][model][chat_index].append((user_query, ai_response, summary))

def add_prompt_summary(llm, query):
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    init_Prompt = """
    Please analyze the user's question and summarize it into 10 Taiwan Chinese characters: \
    {query}
    """
    input_prompt = PromptTemplate(input_variables=["query"], template=init_Prompt)
    return LLMChain(prompt=input_prompt, llm=llm)

def summarize_query(llm, query):
    llm = define_llm(openai_api_base, model, openai_api_key)
    llm_chain = add_prompt_summary(llm, query)
    result = llm_chain.invoke({"query": query})
    return result['text']

def load_documents():
    loader = DirectoryLoader(TMP_DIR.as_posix(), glob='**/*.pdf')
    documents = loader.load()
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)
    return texts

def embeddings_on_local_vectordb(texts):
    embeddings = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")
    vectordb = Chroma.from_documents(texts, embedding=embeddings,
                                     persist_directory=LOCAL_VECTOR_STORE_DIR.as_posix())
    vectordb.persist()
    retriever = vectordb.as_retriever(search_kwargs={'k': 7})
    return retriever

def define_llm(openai_api_base, model, openai_api_key):
    if openai_api_key == 'None':
        llm = Ollama(base_url=openai_api_base, model=model)
    else:
        llm = ChatOpenAI(openai_api_key=openai_api_key, openai_api_base=openai_api_base)
    return llm

def query_llm(retriever, query):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=define_llm(openai_api_base, model, openai_api_key),
        retriever=retriever,
        return_source_documents=True,
    )
    result = qa_chain({'question': query, 'chat_history': st.session_state['chat_history'][st.session_state['mode']][st.session_state['current_model']][st.session_state['current_chat_index']]})
    result_text = result['answer']
    
    llm = define_llm(openai_api_base, model, openai_api_key)
    summary = summarize_query(llm, result_text)
    
    execute_query("INSERT INTO chat_history (conversation_id, mode, model, chat_index, user_query, ai_response, summary) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (st.session_state['conversation_id'], st.session_state['mode'], st.session_state['current_model'], st.session_state['current_chat_index'], query, result_text, summary))
    st.session_state['chat_history'][st.session_state['mode']][st.session_state['current_model']][st.session_state['current_chat_index']].append((query, result_text, summary))
    return result_text

def query_llm_direct(query):
    llm = define_llm(openai_api_base, model, openai_api_key)
    llm_chain = add_prompt(llm, query)
    result = llm_chain.invoke({"query": query})
    result_text = result['text']
    
    mode = st.session_state['mode']
    current_model = st.session_state['current_model']
    current_chat_index = st.session_state['current_chat_index']
    
    summary = summarize_query(llm, query)
    
    if current_model in st.session_state['chat_history'][mode] and len(st.session_state['chat_history'][mode][current_model]) > current_chat_index:
        chat_history = st.session_state['chat_history'][mode][current_model][current_chat_index]
        if not any(query == msg[0] for msg in chat_history):
            chat_history.append((query, result_text, summary))
            execute_query("INSERT INTO chat_history (conversation_id, mode, model, chat_index, user_query, ai_response, summary) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                          (st.session_state['conversation_id'], mode, current_model, current_chat_index, query, result_text, summary))
    else:
        if current_model not in st.session_state['chat_history'][mode]:
            st.session_state['chat_history'][mode][current_model] = [[]]
        if len(st.session_state['chat_history'][mode][current_model]) <= current_chat_index:
            st.session_state['chat_history'][mode][current_model].append([])
        st.session_state['chat_history'][mode][current_model][current_chat_index].append((query, result_text, summary))
        execute_query("INSERT INTO chat_history (conversation_id, mode, model, chat_index, user_query, ai_response, summary) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (st.session_state['conversation_id'], mode, current_model, current_chat_index, query, result_text, summary))
    
    return result_text

def add_prompt(llm, query):
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    init_Prompt = """
    you are helpful, kind, honest, good at writing, and never fail to answer any requests immediately and with precision. \
    Provide an answer in Taiwan Chinese only to the following question in about 150 words. Ensure that the answer is informative, \
    relevant, and concise: \
    {query}
    """
    input_prompt = PromptTemplate(input_variables=["query"], template=init_Prompt)
    return LLMChain(prompt=input_prompt, llm=llm)

def input_fields():
    st.session_state.source_docs = st.file_uploader(label="上傳文件", type="pdf", accept_multiple_files=True)

def process_documents():
    try:
        for source_doc in st.session_state.source_docs:
            with tempfile.NamedTemporaryFile(delete=False, dir=TMP_DIR.as_posix(), suffix='.pdf') as tmp_file:
                tmp_file.write(source_doc.read())
                pdf_path = tmp_file.name
            
            documents = load_documents()
            
            for _file in TMP_DIR.iterdir():
                temp_file = TMP_DIR.joinpath(_file)
                temp_file.unlink()
            
            texts = split_documents(documents)
            st.session_state.retriever = embeddings_on_local_vectordb(texts)
            
            embeddings_path = LOCAL_VECTOR_STORE_DIR.joinpath('chroma-embeddings.parquet').as_posix()
            execute_query("INSERT INTO pdf_uploads (pdf_path, embeddings_path) VALUES (?, ?)", (pdf_path, embeddings_path))
            
    except Exception as e:
        st.error(f"An error occurred: {e}")

def delete_chat_history_and_update_indexes(mode, model, delete_index):
    execute_query("DELETE FROM chat_history WHERE mode = ? AND model = ? AND chat_index = ?", 
                  (mode, model, delete_index))
    
    chat_histories = fetch_query("SELECT id, chat_index FROM chat_history WHERE mode = ? AND model = ? ORDER BY chat_index", 
                                 (mode, model))
    
    for chat_id, chat_index in chat_histories:
        if chat_index > delete_index:
            new_index = chat_index - 1
            execute_query("UPDATE chat_history SET chat_index = ? WHERE id = ?", (new_index, chat_id))
    
    # 更新 session_state 中的 chat_history
    if model in st.session_state['chat_history'][mode]:
        st.session_state['chat_history'][mode][model] = [chat for i, chat in enumerate(st.session_state['chat_history'][mode][model]) if i != delete_index]
        st.session_state['chat_history'][mode][model] = [[(msg[0], msg[1], msg[2]) for msg in chat] for chat in st.session_state['chat_history'][mode][model]]
        st.session_state['current_chat_index'] = min(st.session_state['current_chat_index'], len(st.session_state['chat_history'][mode][model]) - 1)

def boot():
    input_fields()
    st.markdown(f"""
        <style>
            div.stButton > button.submit-button {{
                background-color: #ffffff;
                border: 1px solid #d4d4d4;
                border-radius: 5px;
                color: #000;
                font-weight: bold;
                margin: 5px 0;
                padding: 5px 10px; /* Smaller size */
                width: auto;
                text-align: center;
            }}
            div.stButton > button.submit-button:hover {{
                background-color: #f0f0f0;
                border-color: #c0c0c0;
            }}
        </style>
        """, unsafe_allow_html=True)


    
    st.button("提交文件", on_click=process_documents, key="submit", help="提交文件", type='secondary')
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    results = fetch_query("SELECT user_query, ai_response FROM chat_history WHERE mode = ? AND model = ? AND chat_index = ?", 
                          (st.session_state['mode'], st.session_state['current_model'], st.session_state['current_chat_index']))
    for result in results:
        with st.chat_message("user"):
            st.markdown(f"**用戶:** {result[0]}")
        with st.chat_message("assistant"):
            st.markdown(f"**AI:** {result[1]}")

    if query := st.chat_input():
        st.chat_message("user").markdown(f"**用戶:** {query}")

        if "retriever" in st.session_state:
            response = query_llm(st.session_state.retriever, query)
        else:
            response = query_llm_direct(query)

        st.chat_message("ai").write(response)

        if not any(query == msg[0] for msg in st.session_state['chat_history'][st.session_state['mode']][st.session_state['current_model']][st.session_state['current_chat_index']]):
            st.session_state['chat_history'][st.session_state['mode']][st.session_state['current_model']][st.session_state['current_chat_index']].append((query, response))
        st.experimental_rerun()

if __name__ == '__main__':
    login_page()
    if st.session_state["authentication_status"]:
        init_db()
        model, openai_api_base, openai_api_key = main_page()
        boot()
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
        st.warning('Please enter your username and password')