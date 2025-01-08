from langchain_openai import ChatOpenAI
# from langchain.llms import Ollama
# from langchain_community.chat_models import ChatOllama

def llm(model,openai_api_base):
    # llm = ChatOllama(base_url=openai_api_base, model=model)
    llm = ChatOpenAI(api_key="ollama",model=model,base_url=openai_api_base)
    return llm