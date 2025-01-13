# pip install langchain langchain_community
from langchain_community.llms import Ollama

class LLMAPI:
    def __init__(self):
        # 設定 Ollama 伺服器的 Base URL
        self.api_base = "http://10.5.61.81:11437"
        # 可用的模型名稱
        self.llm_model_names = {
            "Gemma2:27b":             "gemma2:27b-instruct-q5_0",  # 推薦1
            "Gemma2":                 "gemma2:latest",
            "Taiwan-llama3-f16":      "cwchang/llama-3-taiwan-8b-instruct:f16",   # 推薦2
            "Taide-llama3-8b-f16":    "jcai/llama3-taide-lx-8b-chat-alpha1:f16",
            "llama3.2:1b":            "llama3.2:1b",
            "llama3.1":               "llama3.1:latest"
        }

    def local_llm(self, model_name: str, query: str) -> str:
        """
        使用指定的 model_name 與 query 去呼叫內部 LLM。
        """
        try:
            # 選擇 LLM
            model = self.llm_model_names.get(model_name)
            llm = Ollama(base_url=self.api_base, model=model)
            return llm.invoke(query)

        except Exception as e:
            return f"查詢失敗: {str(e)}"


if __name__ == "__main__":
    # 測試
    query_text = "你好，請介紹LLM"
    response = LLMAPI().local_llm("Gemma2:27b", query_text)
    print(response)

    # 11437 所有模型名稱:
    #####################################################################################
    # NAME                                       ID              SIZE      MODIFIED
    # llama3.1:latest                            46e0c10c039e    4.9 GB    2 weeks ago
    # llama3.2:1b                                baf6a787fdff    1.3 GB    4 weeks ago
    # jcai/llama3-taide-lx-8b-chat-alpha1:f16    76ba6fda2ac0    16 GB     4 weeks ago
    # gemma2:latest                              ff02c3702f32    5.4 GB    4 weeks ago
    # gemma2:27b-instruct-q5_0                   9a3c9159e872    18 GB     4 weeks ago
    # cwchang/llama-3-taiwan-8b-instruct:f16     86eb0c227868    16 GB     4 weeks ago
    ####################################################################################