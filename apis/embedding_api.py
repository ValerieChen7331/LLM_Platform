from langchain_community.embeddings import OllamaEmbeddings

class EmbeddingAPI:
    @staticmethod
    def get_embedding_function():
        # 獲取 embedding 函數
        embedding = OllamaEmbeddings(base_url="http://10.5.61.81:11435", model="llama3")
        return embedding
