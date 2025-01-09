from langchain_community.embeddings import OllamaEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
import streamlit as st
from dotenv import load_dotenv
import os

class EmbeddingAPI:

    @staticmethod
    def get_embedding_function():
        """選擇內部或外部 LLM 模型來獲取 embeddings"""
        mode = st.session_state.get('mode', '內部LLM')

        if mode == '內部LLM':
            return EmbeddingAPI._get_internal_embeddings()
        else:
            return EmbeddingAPI._get_external_embeddings()

    @staticmethod
    def _get_internal_embeddings():
        """獲取內部 LLM 模型的 embeddings"""
        # 定義內部可用的 embedding 模型與 base_url
        embedding_models = {
            "llama3": "http://10.5.61.81:11435",
            "bge-m3": "http://10.5.61.81:11435"
        }

        # 獲取 session 中的模型設定，若無則設為 'llama3'
        model = st.session_state.get('embedding', 'llama3')

        # 檢查模型名稱是否有效
        base_url = embedding_models.get(model)
        if not base_url:
            raise ValueError(f"無效的內部模型名稱：{model}")

        # 建立並返回 OllamaEmbeddings 實例
        embeddings = OllamaEmbeddings(base_url=base_url, model=model)

        # 更新 session 中的模型名稱
        st.session_state['embedding'] = model
        return embeddings

    @staticmethod
    def _get_external_embeddings():
        """獲取外部 Azure 模型的 embeddings"""
        # 獲取 session 中的外部模型設定，若無則設為 'text-embedding-ada-002'
        model = st.session_state.get('embedding', 'text-embedding-ada-002')
        # 加载 .env 文件中的环境变量
        load_dotenv()

        # 从环境变量中获取 API Key、Endpoint 和 API 版本
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "bb8634b9b3254065b567d3a451efa7d2")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT", "https://azure-tese1-gpt4.openai.azure.com/")
        embedding_api_version = os.getenv("Embedding_API_VERSION", "2023-05-15")

        # 使用 Azure OpenAI API 來建立 embeddings
        embeddings = AzureOpenAIEmbeddings(
            model=model,
            azure_endpoint=api_base,
            api_key=api_key,
            openai_api_version=embedding_api_version,
            # dimensions: Optional[int] = None  # 可選擇指定新 text-embedding-3 模型的維度
        )

        # 更新 session 中的模型名稱
        st.session_state['embedding'] = model
        return embeddings
