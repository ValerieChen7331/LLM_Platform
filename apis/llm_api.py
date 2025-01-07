from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama

class LLMAPI:
    @staticmethod
    def get_llm(model, api_base, api_key):
        if api_key == 'None':
            return Ollama(base_url=api_base, model=model)
        return ChatOpenAI(openai_api_base=api_base, openai_api_key=api_key)
