from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
import streamlit as st


class LLMAPI:
    models = {
        "Llama-3-8b": "qwen2:7b",
        "taiwan-llama-3-8b": "SimonPu/llama-3-taiwan-8b-instruct-dpo",
        "taiwan-llm-13b": "wangrongsheng/taiwanllm-13b-v2.0-chat",
        "gemma2-9b-chinese": "wangshenzhi/gemma2-9b-chinese-chat"
    }

    @staticmethod
    def get_llm():
        mode = st.session_state.get('mode', 'default_mode')

        if mode == '內部LLM':
            api_base = 'http://10.5.61.81:11434'
            option = st.session_state.get('option', 'Llama-3-8b')
            model = LLMAPI.models[option]
            st.session_state['model'] = model
            return Ollama(base_url=api_base, model=model)

        else:
            api_base = st.session_state.get('api_base', None)
            api_key = st.session_state.get('api_key', None)
            if not api_base or not api_key:
                raise ValueError("外部 LLM: 請輸入 API 地址 和 API 密鑰.")
            return ChatOpenAI(openai_api_base=api_base, openai_api_key=api_key)
