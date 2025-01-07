import streamlit as st
import pandas as pd
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from apis.llm_api import LLMAPI
from apis.file_paths import FilePaths

class LLMModel:
    def __init__(self):
        self.file_paths = FilePaths()
        self.tmp_dir, self.vector_store_dir, self.output_dir = self.file_paths.get_doc_paths()

    def define_llm(self, model, api_base, api_key):
        return LLMAPI.get_llm(model, api_base, api_key)

    def rag_prompt(self):
        init_prompt = """
        請根據以下資訊回答問題，若下列資訊不足，請如實告知，勿自行編造: \
        {sources}\
        請根據上述資訊，用繁體中文回答\
        {query}
        """
        return PromptTemplate(input_variables=["query", "sources"], template=init_prompt)

    def llm_direct_prompt(self):
        init_prompt = """
        請直接回答問題，並使用繁體中文: {query}
        """
        return PromptTemplate(input_variables=["query"], template=init_prompt)

    def query_llm_rag(self, retriever, query, model, api_base, api_key):
        try:
            llm = self.define_llm(model, api_base, api_key)
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                return_source_documents=True
            )

            result = qa_chain.invoke({'question': query, 'chat_history': st.session_state.get('messages', [])})
            retrieved_documents = result.get('source_documents', [])

            prompt_template = self.rag_prompt()
            sources = "\n\n".join([doc.page_content for doc in retrieved_documents])
            formatted_prompt = prompt_template.format(query=query, sources=sources)

            result_text = llm.invoke(formatted_prompt)

            st.session_state.messages.append((query, result_text))
            self.save_retrieved_data_to_csv(query, retrieved_documents, result_text)

            return result_text, retrieved_documents

        except Exception as e:
            st.error(f"Error querying LLM: {e}")
            return "An error occurred while querying the LLM.", []

    def query_llm_direct(self, query, model, api_base, api_key):
        try:
            llm = self.define_llm(model, api_base, api_key)
            prompt_template = self.llm_direct_prompt()
            formatted_prompt = prompt_template.format(query=query)

            result_text = llm.invoke(formatted_prompt)

            return result_text

        except Exception as e:
            st.error(f"Error querying LLM directly: {e}")
            return "An error occurred while querying the LLM directly."

    def save_retrieved_data_to_csv(self, query, retrieved_data, result_text):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir.joinpath('retrieved_data.csv')

        new_data = {
            "Question": [query] * len(retrieved_data),
            "Document": [f"文檔 {i + 1}" for i in range(len(retrieved_data))],
            "Content": [data.page_content for data in retrieved_data],
            "Result": [result_text] * len(retrieved_data)
        }
        new_df = pd.DataFrame(new_data)

        if output_file.exists():
            existing_df = pd.read_csv(output_file)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df

        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
