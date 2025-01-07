# RAG_LangChain_streamlit_MVC
## 專案目錄結構
```plaintext
project/
│
├── app.py                             # 主應用程序，負責配置頁面和初始化控制器
│
├── controllers/                       # 控制器層，負責處理用戶輸入和調用服務
│   ├── ui_controller.py               # UI 控制器
│
├── services/                          # 服務層，包含業務邏輯和與模型的交互
│   ├── document_services.py           # 文件服務
│   ├── llm_services.py                # LLM 服務
│
├── models/                            # 模型層，處理數據操作和邏輯
│   ├── database_model.py              # 資料庫模型
│   ├── document_model.py              # 文件模型
│   ├── llm_model.py                   # LLM 模型
│
├── apis/                              # API 層，負責與外部服務進行交互
│   ├── llm_api.py                     # LLM API
│   ├── embedding_api.py               # 嵌入 API
│   ├── file_paths.py                  # 文件路徑和數據儲存處理
│
├── data/                              # 數據文件夾，包含臨時和持久化的數據存儲
│   ├── chat_history.db                # 聊天記錄資料庫
│
├── views/                             # 視圖層，負責頁面顯示和用戶互動
│   ├── login_page.py                  # 登錄頁面
│   ├── main_page.py                   # 主頁面
```

## 詳細說明

### 1. View（視圖層）
- **`app.py`**: 主應用程序文件，負責配置頁面和初始化控制器，啟動應用程式。
- **`views/`**: 包含應用的視圖層，處理頁面的顯示和用戶交互：
  - **`login_page.py`**: 登錄頁面邏輯。
  - **`main_page.py`**: 主頁面邏輯。


### 2. Controller（控制器層）
- **`ui_controller.py`**: UI 控制器，負責處理來自視圖層的請求，調用服務層來執行業務邏輯，並將結果返回給視圖層。


### 3. Services（服務層）
服務層負責處理業務邏輯，與模型層交互，並將結果返回給控制器層。
- **`document_services.py`**: 文件服務，負責處理文件的加載、拆分、嵌入等操作的業務邏輯。
- **`llm_services.py`**: LLM 服務，負責處理 LLM 查詢邏輯，調用 LLM 模型以獲取答案。


### 4. Model（模型層）
模型層負責數據操作和邏輯，包括數據的存取、處理和持久化。
- **`database_model.py`**: 資料庫模型，負責處理數據庫的操作。
- **`document_model.py`**: 文件模型，負責處理文件的加載、拆分和嵌入等操作。
- **`llm_model.py`**: LLM 模型，負責與 LLM API 的交互並處理查詢邏輯。


### 5. APIs（API 層）
API 層負責與外部服務進行交互。
- **`llm_api.py`**: LLM API，負責調用外部 LLM 服務。
- **`embedding_api.py`**: 嵌入 API，負責調用嵌入生成服務。
- **`file_paths.py`**: 文件路徑和數據儲存處理，提供統一的文件路徑管理。


### 6. data（數據文件夾）
- **`chat_history.db`**: 聊天記錄資料庫，用於存儲對話歷史數據。

---

## 特性
- 使用 **MVC 架構**，強調模組化和分層設計。
- 數據和邏輯分離，便於維護和擴展。
- 包含完整的 **API 層**，用於與外部服務交互。
