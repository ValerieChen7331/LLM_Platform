from flask import Flask, request, jsonify
from langchain_community.llms import Ollama

app = Flask(__name__)

class LLMAPI:
    @staticmethod
    def get_internal_llm(llm_option):
        # 定義內部 API 基底位址 (API Base URL)
        api_bases = {
            'api_base_34': 'http://10.5.61.81:11434',  # 內部 API 伺服器 34
            'api_base_36': 'http://10.5.61.81:11437'   # 內部 API 伺服器 36
        }

        # 定義可用的 LLM 模型配置
        llm_configurations = {
            "Gemma2:27b": {
                "model": "gemma2:27b-instruct-q5_0",
                "api_base": api_bases['api_base_36']
            },
            "Taiwan-llama3-f16": {
                "model": "cwchang/llama-3-taiwan-8b-instruct:f16",
                "api_base": api_bases['api_base_36']
            },
            "Taiwan-llama3-8b": {
                "model": "SimonPu/llama-3-taiwan-8b-instruct-dpo",
                "api_base": api_bases['api_base_34']
            }
        }

        # 確認選擇的模型是否存在於 llm_configurations 中
        config = llm_configurations.get(llm_option)
        if not config:
            # 若無此模型配置則拋出錯誤
            raise ValueError(f"無效的內部模型選項：{llm_option}")

        # 建立 Ollama 模型實例
        llm = Ollama(base_url=config["api_base"], model=config["model"])
        return llm

@app.route('/api/llm', methods=['POST'])
def get_llm():

    try:
        data = request.json
        llm_option = data.get('llm_option')

        # 檢查是否有提供 llm_option
        if not llm_option:
            return jsonify({"error": "缺少 llm_option 參數"}), 400

        # 取得對應的 LLM 實例
        llm = LLMAPI.get_internal_llm(llm_option)

        user_message = data.get('message', '')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        try:
            response = llm.invoke(user_message)
            return jsonify({'reply': response.content if response and response.content else "No reply."})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 啟動 Flask 應用程式，監聽所有網路介面，並在 5000 埠口提供服務
    app.run(host='0.0.0.0', port=5000)
