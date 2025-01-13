import pandas as pd
import os


def main():
    file_path = "./TaiwanLlama3f16"  # 設置目錄路徑
    # Gemma27b, Gemma2, Taide, TaiwanLlama3, TaiwanLlama3f16, GPT4o_mini
    score_simple = []
    score_complex = []
    file_names = []  # 用來存儲處理過的檔案名稱

    # 確保檔案路徑存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"目錄 {file_path} 不存在")

    # 遍歷目錄中的所有 CSV 文件
    for file_name in os.listdir(file_path):
        if file_name.endswith(".csv"):  # 檢查是否為 CSV 文件
            file_full_path = os.path.join(file_path, file_name)
            try:
                df = pd.read_csv(file_full_path)  # 讀取 CSV 文件
                # 檢查是否存在 'SimilarityScore' 欄位
                if 'SimilarityBoolean' not in df.columns:
                    print(f"文件 {file_name} 中沒有 'SimilarityBoolean' 欄位，跳過該文件。")
                    continue

                # 計算相似度分數
                simple_score = df['SimilarityBoolean'][0:21].sum()
                complex_score = df['SimilarityBoolean'][22:40].sum()
                score_simple.append(simple_score)
                score_complex.append(complex_score)
                file_names.append(file_name)  # 保存檔案名稱
                print(f"1. score_simple for {file_name}: {simple_score}")
                print(f"2. score_complex for {file_name}: {complex_score}")
            except Exception as e:
                print(f"讀取或處理文件 {file_name} 時發生錯誤: {e}")

    # 計算平均值
    avg_simple = sum(score_simple) / len(score_simple) if score_simple else 0
    avg_complex = sum(score_complex) / len(score_complex) if score_complex else 0

    print(f"1. AVG score_simple: {avg_simple}")
    print(f"2. AVG score_complex: {avg_complex}")

    # 保存總結數據到 DataFrame
    summary_data = {
        "File Name": file_names,
        "Score Simple": score_simple,
        "Score Complex": score_complex,
    }
    df_sum = pd.DataFrame(summary_data)

    # 保存到 CSV 文件
    output_file = "summary_scores_TaiwanLlama3f16.csv"
    df_sum.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"總結數據已保存到 {output_file}")


if __name__ == "__main__":
    main()  # 執行主函數
