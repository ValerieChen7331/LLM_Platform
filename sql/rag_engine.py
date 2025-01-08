import os, tempfile
from pathlib import Path

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
import streamlit as st

from sqlagent import agent
from sqlagent2 import agent as agent_II
from sql_test import query as qu

mport yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import json

TMP_DIR = Path(__file__).resolve().parent.joinpath('data', 'tmp')
LOCAL_VECTOR_STORE_DIR = Path(__file__).resolve().parent.joinpath('data', 'vector_store')

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

st.title("南亞塑膠生成式AI")
# st.session_state.selected_model = st.selectbox(
#     "Please select the model:", [model["name"] for model in ol.list()["models"]])

# Initialize the chat history and mode
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'mode' not in st.session_state:
    st.session_state['mode'] = '內部LLM'

if 'agent' not in st.session_state:
    st.session_state['agent'] = '一般助理'


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
    embeddings = OllamaEmbeddings(base_url="http://10.5.61.81:11435",model="llama3")
    # model_name = "sentence-transformers/all-MiniLM-L6-v2"
    # model_kwargs = {'device': 'cpu'}
    # embeddings = HuggingFaceEmbeddings(model_name=model_name,
    #                                 model_kwargs=model_kwargs)
    vectordb = Chroma.from_documents(texts, embedding=embeddings,
                                     persist_directory=LOCAL_VECTOR_STORE_DIR.as_posix())
    vectordb.persist()
    retriever = vectordb.as_retriever(search_kwargs={'k': 7})
    retriever_json = retriever.to_json()  # Example method, actual method depends on your retriever class

    with open(LOCAL_VECTOR_STORE_DIR.as_posix()+'/retriever.json', 'w') as f:
        json.dump(retriever_json, f)
    return retriever

def define_llm(openai_api_base,model,openai_api_key):
    if openai_api_key =='None':
        llm = Ollama(base_url=openai_api_base, model=model)
    else:
        llm = ChatOpenAI(openai_api_key=openai_api_key, openai_api_base=openai_api_base)
    return llm

def query_llm(openai_api_base,model,openai_api_key,retriever, query):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm = define_llm(openai_api_base,model,openai_api_key),
        retriever=retriever,
        return_source_documents=True,
    )
    result = qa_chain({'question': query, 'chat_history': st.session_state.messages})
    result = result['answer']
    st.session_state.messages.append((query, result))
    return result

def query_llm_direct(openai_api_base,model,openai_api_key,query):
    llm = define_llm(openai_api_base,model,openai_api_key)
    llm_chain = add_prompt(llm, query)
    result = llm_chain.invoke({"query": query})
    result = result['text']
    st.session_state.messages.append((query, result))
    return result

def add_prompt(llm, query):
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    init_Prompt = f"""
    you are helpful, kind, honest, good at writing, and never fails to answer any requests immediately and with precision. \
    Provide an answer in Taiwan Chinese only to the following question in about 150 words. Ensure that the answer is informative, \
    relevant, and concise: \
    {query}
    """
    
    input_prompt = PromptTemplate(input_variables=["query"], template=init_Prompt)

    return LLMChain(prompt=input_prompt, llm=llm)

def add_prompt_sql(llm, query):
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    init_Prompt = f"""
    summarize the content below. \
    {query}
    """
    
    input_prompt = PromptTemplate(input_variables=["query"], template=init_Prompt)

    return LLMChain(prompt=input_prompt, llm=llm)

def query_llm_sql(openai_api_base,model,openai_api_key,query):
    llm = define_llm(openai_api_base,model,openai_api_key)
    llm_chain = add_prompt_sql(llm, query)
    result = llm_chain.invoke({"query": query})
    result = result['text']
    st.session_state.messages.append((query, result))
    return result

def input_fields():
    st.session_state.source_docs = st.file_uploader(label="Upload Documents", type="pdf", accept_multiple_files=True)
    st.button("Submit Documents", on_click=process_documents)

def process_documents():
    # if not openai_api_base or not openai_api_key:
    #     st.warning(f"Please provide information about LLM model.")
    # else:
    try:
        for source_doc in st.session_state.source_docs:
            with tempfile.NamedTemporaryFile(delete=False, dir=TMP_DIR.as_posix(), suffix='.pdf') as tmp_file:
                tmp_file.write(source_doc.read())
            documents = load_documents()
            for _file in TMP_DIR.iterdir():
                temp_file = TMP_DIR.joinpath(_file)
                temp_file.unlink()
            texts = split_documents(documents)
            st.session_state.retriever = embeddings_on_local_vectordb(texts)
    except Exception as e:
        st.error(f"An error occurred: {e}")

def boot():
    #
    with st.sidebar:
        st.title("Agent")
        st.session_state['agent'] = st.radio("請選擇助理種類型:", ('一般助理', '個人KM','資料庫查找助理','資料庫查找助理2.0','SQL生成助理'))

    if st.session_state['agent'] != '一般助理' and st.session_state['agent'] != '個人KM':
        options = ["Oracle","MSSQL","SQLITE"]
        db_source = st.sidebar.selectbox('Choose Source:', options)
        if db_source == "Oracle":
            options = ["v2nbfc00_xd_QMS"]
            db_name = st.sidebar.selectbox('Choose db:', options)
            st.write('輸入範例1 \: v2nbfc00_xd_QMS table, 尋找EMPID=N000175896的TEL')
        elif db_source == "MSSQL":
            options = ["NPC_3040"]
            db_name = st.sidebar.selectbox('Choose db:', options)
            if db_name == "NPC_3040":
                st.write('輸入範例1 \: anomalyRecords on 2023-10-10 10:40:01.000')
            else:
                pass
        elif db_source == "SQLITE":
            options = ["CC17","netincome"]
            db_name = st.sidebar.selectbox('Choose db:', options)
            if db_name == "CC17":
                st.write('輸入範例1 \: CC17中ACCT=8003RZ的第一筆資料')
            else:
                st.write('輸入範例1 \: SALARE=荷蘭的TARIFFAMT總和')
        else:
            db_name ='na'
    # Sidebar for mode selection and chat history
    with st.sidebar:
        st.title("LLM")
        st.session_state['mode'] = st.radio("請選擇內部或外部LLM：", ('內部LLM', '外部LLM'))


    if st.session_state['mode'] == '內部LLM':
        # openai_api_base = st.sidebar.text_input('URL:', type='default')
        options = ["wangrongsheng/taiwanllm-13b-v2.0-chat","qwen2:7b","SimonPu/llama-3-taiwan-8b-instruct-dpo"]
        model = st.sidebar.selectbox('Choose a LLM:', options)
        openai_api_base = 'http://10.5.61.81:11434'
        openai_api_key = 'None'
    elif st.session_state['mode'] == '外部LLM':
        openai_api_base = st.sidebar.text_input('api_base:', type='password')
        openai_api_key = st.sidebar.text_input('key:', type='password')

    with st.sidebar:
        st.title("Chat History")
        for chat in st.session_state['chat_history']:
            st.write(chat)
    if st.session_state['agent'] == '個人KM':
        input_fields()
    #
    if "messages" not in st.session_state:
        st.session_state.messages = []    
    #
    for message in st.session_state.messages:
        st.chat_message('human').write(message[0])
        st.chat_message('ai').write(message[1])    
    #
    if query := st.chat_input():
        st.chat_message("human").write(query)

        
        if st.session_state['agent'] == '資料庫查找助理':
            response = agent(query,db_name,db_source)
        elif st.session_state['agent'] == '資料庫查找助理2.0':
            response = agent_II(query,db_name,db_source)
        elif st.session_state['agent'] == 'SQL生成助理':
            response = qu(query,db_name,db_source)
        elif st.session_state['agent'] == '個人KM':
            response = query_llm(openai_api_base,model,openai_api_key,st.session_state.retriever, query)
        else:
            response = query_llm_direct(openai_api_base,model,openai_api_key,query)

        st.chat_message("ai").write(response)
        # # Optionally, store the new message pair in session state
        # st.session_state.messages.append((query, response))

        # Update chat history in the sidebar
        st.session_state.chat_history.append(f"User: {query}")  
        st.session_state.chat_history.append(f"AI: {response}")

if __name__ == '__main__':
    
    authenticator.login()
    # try:
    #     email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(pre_authorization=True)
    #     if email_of_registered_user:
    #         st.success('User registered successfully')
    #         with open('login_config.yaml', 'w') as file:
    #             yaml.dump(config, file, default_flow_style=False)
    # except Exception as e:
    #     st.error(e)
    if st.session_state['authentication_status']:
        authenticator.logout()
        st.write(f'Welcome *{st.session_state["name"]}*')
        boot()
    elif st.session_state['authentication_status'] is False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] is None:
        st.warning('Please enter your username and password')
    