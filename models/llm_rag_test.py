import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 初始化語言模型，使用 "gpt-3.5-turbo" 模型，溫度設為 0，確保回答穩定
llm = LLMAPI.get_llm()

# 初始化 embedding_function
self.embedding_function = EmbeddingAPI.get_embedding_function()

### 構建檢索器 ###
documents = load_documents()    # load_documents()

# 使用文本分割器來將文件分割成較小的部分
# split_documents_into_chunks(self, documents)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(documents)

# 建立 Chroma 向量庫並將分割後的文檔轉換成嵌入向量
#embeddings_on_local_vectordb(self, document_chunks)
# llm_model
vectorstore = Chroma.from_documents(documents=splits, embedding=self.embedding_function)

# llm_model
retriever = vectorstore.as_retriever()

### 將問題與上下文整合 ###
# 系統提示，用於重構問題，考慮到聊天記錄，讓問題可以獨立理解
contextualize_q_system_prompt = """
    根據聊天記錄和最新的使用者問題，\
    該問題可能參考了聊天記錄中的上下文，請將其重構為一個可以不依賴聊天記錄就能理解的問題。\
    不要回答問題，只需重新表述，若無需表述則保持不變。
"""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# 創建具備聊天記錄感知能力的檢索器
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

### 回答問題 ###
# 系統提示，用於回答問題，根據檢索到的上下文進行回答
qa_system_prompt = """
    您是回答問題的助手。\
    使用以下檢索到的內容來回答問題。\
    如果您不知道答案，請直接說您不知道。    
    {context}
"""
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# 創建問題回答鏈
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

# 建立檢索增強生成（RAG）的問答鏈
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

### 管理聊天記錄 ###
# 狀態管理聊天記錄的儲存

chat_history_data = st.session_state.get('chat_history', [])
if chat_history_data:
    chat_history = ChatMessageHistory()
    for record in chat_history_data:
        user_query, ai_response = record['user_query'], record['ai_response']
        chat_history.add_user_message(user_query)
        chat_history.add_ai_message(ai_response)
else:

# 創建具聊天記錄功能的檢索增強生成鏈，包含輸入與歷史訊息的關聯
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    chat_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)
