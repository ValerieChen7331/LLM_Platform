from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from langchain_community.llms import Ollama
import streamlit as st

class LLMAPI:
    # 定義內部 LLM 模型選項
    models = {
        "Qwen2-Alibaba": "qwen2:7b",
        # Traditional Mandarin
        "Taiwan-llama3-8b": "SimonPu/llama-3-taiwan-8b-instruct-dpo",
        # Traditional Mandarin---時好時壞----
        "Taiwan-llama2-13b": "wangrongsheng/taiwanllm-13b-v2.0-chat"
    }
    @staticmethod
    def get_llm():
        """根據模式選擇內部或外部 LLM"""
        mode = st.session_state.get('mode', '內部LLM')
        llm_option = st.session_state.get('llm_option', 'Qwen2-Alibaba')

        if mode == '內部LLM':
            return LLMAPI._get_internal_llm(llm_option)
        else:
            return LLMAPI._get_external_llm(llm_option)
    @staticmethod
    def _get_internal_llm(llm_option):
        """獲取內部 LLM 模型"""
        api_base = 'http://10.5.61.81:11434'

        # 確認選擇的模型是否有效
        model = LLMAPI.models.get(llm_option)
        if not model:
            raise ValueError(f"無效的內部模型選項：{llm_option}")

        # 更新 session_state 中的模型選項
        st.session_state['model'] = model

        # Ollama 模型實例
        llm = Ollama(base_url=api_base, model=model)
        return llm

    @staticmethod
    def _get_external_llm(deployment_name):
        """獲取外部 Azure LLM 模型"""
        # 加载 .env 文件中的环境变量
        load_dotenv()

        # 从环境变量中获取 API Key、Endpoint 和 API 版本
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        print("1",api_key)
        print("2",api_base)
        print("3",api_version)

        if not all([api_key, api_base, api_version]):
            raise ValueError("缺少API Key、Endpoint 或 API Version")

        # 初始化 Azure ChatOpenAI 模型
        llm = AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=api_base,
            api_version=api_version,
            deployment_name=deployment_name
        )
        return llm

    @staticmethod
    def _get_gemini(deployment_name):
        """獲取外部 Gemini 模型"""
        from langchain_google_genai import ChatGoogleGenerativeAI

        # 使用 os.getenv() 來取得環境變數中的 API 金鑰
        api_key = os.getenv("GOOGLE_API_KEY")

        # 初始化 Google Gemini 模型
        llm = ChatGoogleGenerativeAI(model="gemini-pro", api_key=api_key)

        return llm