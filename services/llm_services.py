import streamlit as st
from models.llm_model import LLMModel

class LLMService:
    def __init__(self):
        self.llm_model = LLMModel()

    def query(self, query):
        retriever = st.session_state.get('retriever')
        model = st.session_state.get('model')
        api_base = st.session_state.get('api_base')
        api_key = st.session_state.get('api_key')

        if retriever:
            response, retrieved_data = self.llm_model.query_llm_rag(retriever, query, model, api_base, api_key)
        else:
            response = self.llm_model.query_llm_direct(query, model, api_base, api_key)

        return response
