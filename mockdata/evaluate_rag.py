import pandas as pd
import logging
from apis.llm_api import LLMAPI
import sqlite3
import json


class ResponseEvaluator:
    """
    回應評估類別，負責整體流程：讀取資料、評估回應、儲存結果。
    """

    def __init__(self, input_file: str, output_file: str, mode: str, llm_option: str, evaluation_attempts: int = 3):
        """
        初始化 ResponseEvaluator。

        :param input_file: 輸入檔案路徑
        :param output_file: 輸出檔案路徑
        :param mode: 模式選擇（內部或外部模型）
        :param llm_option: 模型名稱
        :param evaluation_attempts: 評估嘗試次數（預設 3 次以提高穩定性）
        """
        self.input_file = input_file  # 輸入檔案路徑
        self.output_file = output_file  # 輸出檔案路徑
        self.evaluation_attempts = evaluation_attempts  # 評估次數
        try:
            self.llm = LLMAPI.get_llm(mode, llm_option)  # 初始化 LLM
        except Exception as e:
            logging.error(f"無法初始化 LLM：{e}")
            raise

        # 定義評估提示模板
        self.prompt_template = """        
        請比較以下內容，並回答「*T」或「*F」：
        1. 是否完整包含所有必要資訊和核心內容？確認「實際回應」是否涵蓋「答案」中的所有關鍵資訊，未遺漏重要內容。
        2. 是否允許內容超出但未缺少必要資訊？若「實際回應」增加了補充性資訊，但「答案」的必要內容未缺少，則符合要求。
        3. 是否檢查連結、數字相同？ 確保連結、數字正確。
        4. 不拘泥於文字形式，確保意思和關鍵信息一致即可，不要求完全相同的文字表述。
        5. 請列出思考過程，並給出結論，若「實際回應」正確，返回「*t」，若「實際回應」錯誤，則返回「*f」。
        6. 最後輸出: final_answer:
        ---
        (1.) 問題: {query}
        (2.) 答案：{expected_response}
        (3.) 實際回應：{generated_response}
        """

    def run(self):
        """
        主流程：讀取資料、進行評估、儲存結果。
        """
        logging.info("讀取原始檔案...")
        df = self._load_data()
        logging.info("原始資料預覽：\n%s", df.head())

        logging.info("開始評估回應...")
        df = self._evaluate_responses(df)

        logging.info("儲存結果...")
        self._save_data(df)
        self._save_to_db(df)

        logging.info("更新後的資料預覽：\n%s", df.head())
        logging.info("結果已儲存至 %s", self.output_file)

    def _load_data(self) -> pd.DataFrame:
        """
        從 CSV 檔案載入資料。

        :return: pandas DataFrame
        """
        try:
            return pd.read_csv(self.input_file)
        except FileNotFoundError:
            logging.error(f"無法找到檔案：{self.input_file}")
            raise
        except pd.errors.EmptyDataError:
            logging.error(f"檔案為空：{self.input_file}")
            raise

    def _evaluate_responses(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        多次評估 DataFrame 中的回應，取平均值以提升評估穩定性。

        :param df: pandas DataFrame，包含預期回應與實際回應
        :return: 更新後的 DataFrame，新增相似度分數欄位
        """
        evaluations = []

        # 多次評估（根據設定的嘗試次數），提高模型回應穩定性
        for attempt in range(self.evaluation_attempts):
            scores = [
                self._evaluate_single_response(row['Question'], row['Answer'], row['Test'])
                for _, row in df.iterrows()
            ]
            evaluations.append(scores)

        print('1. evaluations: ', evaluations)

        # 計算每列的平均分數
        average_scores = [
            sum(score_list) / len(score_list)
            for score_list in zip(*evaluations)
        ]
        # 平均分數 > 0.5 即為 True，並新增欄位
        df['SimilarityScore'] = average_scores
        df['SimilarityBoolean'] = [score > 0.5 for score in average_scores]
        return df

    def _evaluate_single_response(self, query: str, expected_response: str, generated_response: str) -> float:
        """
        使用模型評估單一回應是否包含預期回應的必要內容。

        :param query: 問題文字
        :param expected_response: 預期回應文字
        :param generated_response: 實際回應文字
        :return: 分數（0 或 1 表示是否符合預期）
        """
        prompt = self.prompt_template.format(
            query=query,
            expected_response=expected_response,
            generated_response=generated_response
        )

        try:
            evaluation_result = self.llm.invoke(prompt).content.strip().lower()

            print('2. evaluation_result: ', evaluation_result)

            # 解析回應中的 final_answer
            final_answer = evaluation_result.split('final_answer:')[-1].strip()  # 取最後部分並去除空格

            # 判斷模型回應是否為 true 或 false
            if "*t" in final_answer:
                print("\033[92m" + f"Response: {evaluation_result}" + "\033[0m")  # 綠色輸出
                return 1
            elif "*f" in final_answer:
                print("\033[91m" + f"Response: {evaluation_result}" + "\033[0m")  # 紅色輸出
                return 0
            else:
                raise ValueError("無法判斷模型回應結果，應為 '*t' 或 '*f'。")
        except Exception as e:
            logging.error(f"評估單一回應時發生錯誤：{e}")
            return 0


    def _save_data(self, df: pd.DataFrame):
        """
        將更新後的 DataFrame 儲存為 CSV 檔案。

        :param df: pandas DataFrame，已新增相似度分數欄位
        """
        try:
            df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        except Exception as e:
            logging.error(f"儲存資料時發生錯誤：{e}")
            raise

    def _save_to_db(self, df: pd.DataFrame):
        """
        將 DataFrame 資料保存到資料庫，確保表格結構正確並添加自動遞增主鍵。
        """
        database_path = self.output_file.replace('.csv', '.db')  # 將輸出檔案路徑轉為資料庫路徑

        # 定義表格結構
        table_schema = """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 自動遞增的主鍵
            QA_No INTEGER,
            Question TEXT,
            Answer TEXT,
            Test TEXT,
            SimilarityScore REAL,
            SimilarityBoolean INTEGER,
            Docs TEXT
        )
        """

        try:
            # 將 Docs 欄位的字典轉為 JSON 字串
            if 'Docs' in df.columns:
                logging.info("將 Docs 欄位字典轉為 JSON 字串...")
                df['Docs'] = df['Docs'].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else x)

            # 建立資料庫連線
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()

                # 確保表格存在
                logging.info("檢查並創建資料表...")
                cursor.execute(table_schema)
                conn.commit()

                # 插入新數據
                logging.info("將資料插入資料表中...")
                df.to_sql('evaluations', conn, if_exists='append', index=False)
                logging.info("結果已成功保存至資料庫。")
        except sqlite3.OperationalError as op_err:
            logging.error(f"資料庫操作錯誤：{op_err}")
            raise
        except Exception as e:
            logging.error(f"無法保存資料至資料庫：{e}")
            raise

    def _save_to_db_1(self, df: pd.DataFrame):
        """
        將 DataFrame 資料保存到資料庫，確保表格結構正確並添加自動遞增主鍵。
        """
        database_path = self.output_file.replace('.csv', '.db')  # 將輸出檔案路徑轉為資料庫路徑

        # 定義表格結構
        table_schema = """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 自動遞增的主鍵
            QA_No INTEGER,
            Question TEXT,
            Answer TEXT,
            Test TEXT,
            SimilarityScore REAL,
            SimilarityBoolean INTEGER,
            Docs TEXT
        )
        """

        try:
            # 建立資料庫連線
            with sqlite3.connect(database_path) as conn:
                cursor = conn.cursor()

                # 確保表格存在
                logging.info("檢查並創建資料表...")
                cursor.execute(table_schema)
                conn.commit()

                # 插入新數據
                logging.info("將資料插入資料表中...")
                df.to_sql('evaluations', conn, if_exists='append', index=False)
                logging.info("結果已成功保存至資料庫。")
        except sqlite3.OperationalError as op_err:
            logging.error(f"資料庫操作錯誤：{op_err}")
            raise
        except Exception as e:
            logging.error(f"無法保存資料至資料庫：{e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 配置檔案路徑
    INPUT_FILE_PATH = './mockdata/input.csv'  # 輸入檔案路徑
    OUTPUT_FILE_PATH = './mockdata/output.csv'  # 輸出檔案路徑

    # 初始化 ResponseEvaluator 並執行
    evaluator = ResponseEvaluator(
        input_file=INPUT_FILE_PATH,
        output_file=OUTPUT_FILE_PATH,
        mode="外部LLM",
        llm_option="gpt-4o",
        evaluation_attempts=3  # 設定評估嘗試次數
    )
    evaluator.run()
