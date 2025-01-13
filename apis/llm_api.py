from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from langchain_community.llms import Ollama

class LLMAPI:
    @staticmethod
    def get_llm(mode, llm_option):
        """根據模式選擇內部或外部 LLM"""
        # mode = self.chat_session_data.get("mode")
        # llm_option = self.chat_session_data.get("llm_option")
        if mode == '內部LLM':
            return LLMAPI._get_internal_llm(llm_option)
        else:
            return LLMAPI._get_external_llm(llm_option)

    @staticmethod
    def _get_internal_llm(llm_option):
        """獲取內部 LLM 模型"""
        api_base = 'http://10.5.61.81:11434'

        # 定義內部 LLM 模型選項
        llm_models = {
            "Qwen2-Alibaba": "qwen2:7b",
            # Traditional Mandarin
            "Taiwan-llama3-8b": "SimonPu/llama-3-taiwan-8b-instruct-dpo",
            # Traditional Mandarin---時好時壞----
            "Taiwan-llama2-13b": "wangrongsheng/taiwanllm-13b-v2.0-chat"
        }
        # 確認選擇的模型是否有效
        model = llm_models.get(llm_option)
        if not model:
            raise ValueError(f"無效的內部模型選項：{llm_option}")

        # Ollama 模型實例
        llm = Ollama(base_url=api_base, model=model)
        return llm

    @staticmethod
    def _get_external_llm(llm_option):
        """獲取外部 Azure LLM 模型"""
        deployment_name = llm_option
        # 加载 .env 文件中的环境变量
        load_dotenv()

        # 从环境变量中获取 API Key、Endpoint 和 API 版本
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")

        if not all([api_key, api_base, api_version]):
            raise ValueError("缺少API Key、Endpoint 或 API Version")

        # 初始化 Azure ChatOpenAI 模型
        llm = AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=api_base,
            api_version=api_version,
            deployment_name=deployment_name
        )
        return llm
