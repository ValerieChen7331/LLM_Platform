import pandas as pd
from apis.llm_api import LLMAPI


class ResponseEvaluator:
    """
    回應評估類別，負責整體流程：讀取資料、評估回應、儲存結果。
    """

    def __init__(self, input_file: str, output_file: str, mode: str, llm_option: str ):
        """
        初始化 ResponseEvaluator。

        :param input_file: 輸入檔案路徑
        :param output_file: 輸出檔案路徑
        :param llm_option: 模型名稱
        """
        self.input_file = input_file  # 輸入檔案路徑
        self.output_file = output_file  # 輸出檔案路徑
        self.llm = LLMAPI.get_llm(mode, llm_option)
        # 定義評估提示模板
        self.prompt_template = """        
        請比較以下內容：
        (1.) 「實際回應」是否完整「包含」且不遺漏「預期回應」中的所有必要資訊和核心內容？ 
           - 「實際回應」的內容可多於「預期回應」，但不可少於。
           - 若「實際回應」多出的資訊為補充說明（與預期內容無矛盾或衝突），應判定為符合。
        (2.) 檢查所有數字（特別是金額）是否正確無誤。
        (3.) 若有網址（URL），需確認網址的格式與內容正確無誤。
        (4.) 不需拘泥於文字形式，但意思和核心內容必須一致。        
        請注意：
        - 若「實際回應」完整包含「預期回應」的所有必要內容，即使有額外補充說明，請回答「true」。
        - 若缺少必要內容，或多出的資訊與預期內容矛盾，或數字不正確，請回答「false」。
        - 僅返回「true」或「false」，不提供其他解釋或回應。
        ---
        (1.) 問題: {query}
        (2.) 預期回應：{expected_response}
        (3.) 實際回應：{generated_response}
        """

    def run(self):
        """
        主流程：讀取資料、進行評估、儲存結果。
        """
        # 讀取資料
        print("讀取原始檔案...")
        df = self._load_data()
        print("原始資料預覽：")
        print(df.head())

        # 評估回應
        print("開始評估回應...")
        df = self._evaluate_responses(df)

        # 儲存結果
        print("儲存結果...")
        self._save_data(df)
        print("更新後的資料預覽：")
        print(df.head())
        print(f"結果已儲存至 {self.output_file}")

    def _load_data(self) -> pd.DataFrame:
        """
        從 CSV 檔案載入資料。

        :return: pandas DataFrame
        """
        return pd.read_csv(self.input_file)

    def _evaluate_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        逐列評估 DataFrame 中的回應。

        :param df: pandas DataFrame，包含預期回應與實際回應
        :return: 更新後的 DataFrame，新增相似度分數欄位
        """
        gpt_scores = []
        for i in range(3):
            scores = [
                self._evaluate_single_response(row['Question'], row['Answer'], row['Test'])
                for _, row in df.iterrows()
            ]
            gpt_scores.append(scores)

        if sum(scores) > 1.5:
            similarity_scores = True
        else:
            similarity_scores = False

        df['SimilarityScore'] = similarity_scores  # 新增相似度分數欄位
        return df

    def _evaluate_single_response(self, query: str, expected_response: str, generated_response: str) -> bool:
        """
        使用模型評估單一回應是否包含預期回應的必要內容。

        :param actual_response: 實際回應文字
        :param expected_response: 預期回應文字
        :return: 布林值，表示是否符合預期
        """
        # 格式化提示模板
        prompt = self.prompt_template.format(
            query=query, expected_response=expected_response, generated_response=generated_response
        )
        # 呼叫模型進行評估
        # evaluation_result = self.llm.invoke(prompt).strip().lower()
        evaluation_result = self.llm.invoke(prompt).content.strip().lower()
        print('1. prompt: ', prompt)
        print('2. evaluation_result', evaluation_result)

        # 判斷模型回應是否為 true 或 false
        if "true" in evaluation_result:
            print("\033[92m" + f"Response: {evaluation_result}" + "\033[0m")  # 綠色輸出
            return True
        elif "false" in evaluation_result:
            print("\033[91m" + f"Response: {evaluation_result}" + "\033[0m")  # 紅色輸出
            return False
        else:
            raise ValueError("無法判斷模型回應結果，應為 'true' 或 'false'。")

    def _save_data(self, df: pd.DataFrame):
        """
        將更新後的 DataFrame 儲存為 CSV 檔案。

        :param df: pandas DataFrame，已新增相似度分數欄位
        """
        df.to_csv(self.output_file, index=False, encoding='utf-8-sig')


# if __name__ == "__main__":
#     # 配置檔案路徑
#     INPUT_FILE_PATH = './mockdata/input.csv'  # 輸入檔案路徑
#     OUTPUT_FILE_PATH = './mockdata/output.csv'  # 輸出檔案路徑
#
#     # 初始化 ResponseEvaluator 並執行
#     evaluator = ResponseEvaluator(
#         input_file=INPUT_FILE_PATH,
#         output_file=OUTPUT_FILE_PATH,
#         mode="外部LLM",
#         llm_option="gpt-4o"
#     )
#     evaluator.run()
