from langchain_community.embeddings import OllamaEmbeddings
import streamlit as st

class EmbeddingAPI:
    @staticmethod
    def get_embedding_function():
        # 定義可用的 embedding 模型
        embedding_models = {"llama3": "http://10.5.61.81:11435"}

        # 檢查是否有已存在的 embedding 模型設定，若無則設置預設值
        model = st.session_state.get('embedding', 'llama3')

        # 根據 model 名稱獲取對應的 base_url
        base_url = embedding_models[model]
        if not base_url:
            raise ValueError(f"無效的模型名稱：{model}")

        # 建立並返回 OllamaEmbeddings 實例
        embedding = OllamaEmbeddings(base_url=base_url, model=model)
        st.session_state['embedding'] = model
        return embedding
