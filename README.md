# RAG_LangChain_streamlit_MVC
## 專案目錄結構

```plaintext
project/
│
├── rag_engine.py                      # 主應用程序入口
│
├── views/                             # 視圖層，負責渲染用戶界面
│   ├── register_page.py               # 註冊頁面視圖
│   ├── login_page.py                  # 登錄頁面視圖
│   ├── main_page.py                   # 主頁面顯示邏輯
│   ├── main_page_sidebar.py           # 主頁面側邊欄視圖
│   ├── main_page_content.py           # 主頁面主內容視圖
│
├── controllers/                       # 控制器層，負責處理用戶輸入和調用服務
│   ├── ui_controller.py               # UI 控制器
│   ├── initialize.py                  # 設定初始化條件
│
├── services/                          # 服務層，包含業務邏輯和與模型的交互
│   ├── document_services.py           # 文件服務
│   ├── llm_services.py                # LLM 服務
│
├── sql/                               # SQL 文件夾，存儲數據庫相關文件
│   ├── db_connection.py               # 數據庫連接配置
│   ├── excel_to_db.py                 # Excel 導入數據庫腳本
│   ├── llm.py                         # 語言模型腳本
│   ├──prompt.md
│   ├── sql_test.py                    # SQL 測試腳本
│   ├── sql_agent.py                   # SQL 代理腳本
│   ├── sql_agent_v2.py                # SQL 代理腳本 V2
│   ├──vector_db_manager.py
│
├── models/                            # 模型層，處理數據操作和邏輯
│   ├── document_model.py              # 文件模型
│   ├── llm_model.py                   # LLM模型
│   ├── llm_rag.py                     # RAG 模型
│   ├── database_base.py               # 基礎數據庫操作模型
│   ├── database_devOps.py             # 開發運維數據庫模型
│   ├── database_userRecords.py        # 用戶記錄數據庫模型
│
├── apis/                              # API 層，負責與外部服務進行交互
│   ├── llm_api.py                     # LLM API
│   ├── embedding_api.py               # 嵌入 API
│   ├── file_paths.py                  # 文件路徑和數據存儲處理
│
├── data/                              # 資料庫，包含臨時和持久化的資料存儲
│   ├── developer/                     # 開發端數據存儲(可以看到所有使用者)
│   ├── user/                          # 用戶端數據存儲
│       ├── user1                      # 以"使用者名稱"命名此資料夾
│           ├── user1.db               # 歷史紀錄
│           ├── conversation_ID/       # 以"對話視窗ID"命名此資料夾
│               ├── tmp/               # 臨時文件存儲
│               ├── vector_store/      # 向量資料庫
│   ├── output/                        # 儲存 retrieve 搜索到的文件 chunks
│
├── .env                               # 環境變數設定檔
├── docker-compose.yml                 # Docker Compose配置檔
├── login_config.yaml                  # 登錄配置檔
├── CC17.db                            # SQLite資料庫
├── netincome.db                       # SQLite資料庫
├── requirements.txt                   # 套件清單
```
## 詳細說明

### 0. 啟動程式
- **`rag_engine.py`**: 主應用程序文件，負責啟動應用程式。

### 1. View（視圖層）
- **`login_page.py`**: 負責登錄頁面的視圖邏輯。
- **`main_page.py`**: 負責主頁面的渲染和顯示邏輯。
- **`main_page_sidebar.py`**: 主頁面側邊欄的視圖。
- **`main_page_content.py`**: 主頁面主內容的視圖。

### 2. Controller（控制器層）
- **`ui_controller.py`**: UI 控制器，負責處理來自視圖層的請求，調用服務層的業務邏輯，並將結果返回給視圖層。
- **`initialize.py`設定初始化條件。

### 3. Services（服務層）
- **`document_services.py`**: 文件服務，負責處理文件的加載、拆分、嵌入等操作。
- **`llm_services.py`**: LLM 服務，負責處理 LLM 查詢邏輯，並調用模型以獲取答案。

### 4. SQL 文件夾
- **`database_connection.py`**: 配置數據庫連接。
- **`excel_to_database.py`**: 將 Excel 文件導入到數據庫的腳本。
- **`language_model.py`**: 語言模型相關腳本。
- **`sql_test.py`**: 用於測試 SQL 查詢的腳本。
- **`sql_agent.py`**: SQL 查詢代理腳本。
- **`sql_agent_v2.py`**: SQL 查詢代理腳本的升級版本。

### 5. Model（模型層）
- **`document_model.py`**: 文件模型，處理文件數據的邏輯和操作。
- **`llm_model.py`**: 負責與 LLM API 的交互，並處理查詢邏輯。
- **`database_base.py`**: 基礎數據庫操作邏輯。
- **`database_devOps.py`**: 開發運維相關數據庫模型。
- **`database_userRecords.py`**: 用戶數據記錄相關的數據庫模型。

### 6. APIs（API 層）
- **`llm_api.py`**: 負責調用外部 LLM 服務。
- **`embedding_api.py`**: 負責嵌入生成的 API。
- **`file_paths.py`**: 文件路徑管理和數據存儲處理。

### 7. data（數據儲存）
- **`developer/`**: 開發端數據存儲目錄，可查看所有用戶數據。
- **`user/`**: 用戶端數據存儲目錄，每位用戶以其名稱命名資料夾，包含歷史記錄和對話數據。
  - **`user1/`**: 以 "使用者名稱" 命名的資料夾（示例用戶）。
    - **`user1.db`**: 用戶的歷史記錄文件。
    - **`conversation_ID/`**: 以 "對話視窗ID" 命名的資料夾，存儲每個對話相關數據。
      - **`tmp/`**: 臨時文件存儲目錄。
      - **`vector_store/`**: 向量數據存儲目錄。
- **`output/`**: 用於儲存檢索到的文件塊（chunks）。
  - **`retrieved_data.csv`**: 儲存檢索結果的 CSV 文件。

---

## 特性
- 採用 **MVC 架構**，分層清晰，強調模組化設計。
- 提供完善的 **API 層**，支持外部服務交互。
- 支持多種數據存儲方式，包括臨時文件、本地向量數據庫和用戶數據庫。
- 提供 **SQL 助理功能**，用於自動生成和執行 SQL 查詢。
