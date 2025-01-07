from langchain_community.embeddings import OllamaEmbeddings

class EmbeddingAPI:
    @staticmethod
    def get_embedding_function(base_url, model):
        return OllamaEmbeddings(base_url=base_url, model=model)
