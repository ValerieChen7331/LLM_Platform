import pandas as pd
from mockdata.evaluate_rag import ResponseEvaluator
from models.llm_rag import RAGModel


class RagTest:
    """
    使用 RAG 模型進行查詢並生成測試結果，然後進行評估。
    """

    # 配置檔案路徑
    QA_ORIG_PATH = './mockdata/QAData.csv'  # 原始問題檔案路徑

    # 初始化 session 狀態參數，並儲存到 chat_session_data 字典中
    chat_session_data = {
        'conversation_id': "e1903c14-c737-4ecc-bb37-59f51805cffb",
        'num_chat_windows': 1,
        'active_window_index': 0,
        'agent': '個人KM',

        'mode': '內部LLM',       # '內部LLM','外部LLM'
        'llm_option': 'Taiwan-llama3-f16',      # 'Gemma2:27b', "Taiwan-llama3-f16", 'gpt-4o-mini', 'Taide-llama3-8b-f16', Gemma2
        'model': "cwchang/llama-3-taiwan-8b-instruct:f16",  # gemma2:27b-instruct-q5_0', "cwchang/llama-3-taiwan-8b-instruct:f16", 'gpt-4o-mini', 'jcai/llama3-taide-lx-8b-chat-alpha1:f16'

        # 'mode': '外部LLM',  # '內部LLM','外部LLM'
        # 'llm_option': 'gpt-4o-mini',  # 'Gemma2:27b', 'gpt-4o-mini', 'Taide-llama3-8b-f16'
        # 'model': 'gpt-4o-mini',  # gemma2:27b-instruct-q5_0', 'gpt-4o-mini', 'jcai/llama3-taide-lx-8b-chat-alpha1:f16', 'gemma2:latest'

        'api_base': '',
        'api_key': '',
        'embedding': 'bge-m3',
        'doc_names': '',
        'db_name': '',
        'db_source': '',
        'chat_history': [],
        'title': '',
        'upload_time': None,
        'username': "n000191032",  # 設置使用者名稱
        'empty_window_exists': True  # 確保新窗口存在
    }

    @staticmethod
    def process_questions(input_file_path, output_file_path):
        """
        使用檢索增強生成 (RAG) 模型回答問題，並將結果存入檔案。
        """
        # 讀取問題檔案
        print("讀取問題檔案...")
        df = pd.read_csv(RagTest.QA_ORIG_PATH)

        # 初始化 RAG 模型
        llm_rag = RAGModel(RagTest.chat_session_data)

        # 使用 RAG 模型回答問題
        print("開始生成回答...")
        df['Test'], df['Docs'] = zip(*df['Question'].apply(lambda query: llm_rag.query_llm_rag(query)))

        # 將結果存入中間結果檔案
        print("儲存中間結果檔案...")
        df.to_csv(input_file_path, index=False, encoding='utf-8-sig')

    @staticmethod
    def evaluate_answers(input_file_path, output_file_path):
        """
        使用 ResponseEvaluator 對回答進行評估，並儲存最終結果。
        """
        # 初始化 ResponseEvaluator 並執行
        print("開始評估回答...")
        evaluator = ResponseEvaluator(
            input_file=input_file_path,
            output_file=output_file_path,
            mode="外部LLM",
            llm_option="gpt-4o",
            evaluation_attempts=3
        )
        evaluator.run()


def main():
    """
    主程序執行入口：生成回答並進行評估。
    """
    for i in range(3):
        print(f"=== 啟動第 {i+1} 次 RAG 測試 ===")
        input_file_path = f'./mockdata/TaiwanLlama3f16/TaiwanLlama3f16_{i}.csv'  # 中間結果檔案路徑
        output_file_path = f'./mockdata/TaiwanLlama3f16/TaiwanLlama3f16_{i}.csv'  # 輸出結果檔案路徑
        RagTest.process_questions(input_file_path, output_file_path)  # 使用 RAG 模型生成回答
        RagTest.evaluate_answers(input_file_path, output_file_path)  # 對生成的回答進行評估
        print(f"=== 第 {i+1} 次測試完成 ===")


if __name__ == "__main__":
    main()
