project/
│
├── app.py                             # 主應用程序，負責配置頁面和初始化控制器
│
├── controllers/                       # 控制器層，負責處理用戶輸入和調用服務
│   ├── ui_controller.py               # UI 控制器
│
├── services/                           # 服務層，包含業務邏輯和與模型的交互
│   ├── document_services.py            # 文件服務
│   ├── llm_services.py                 # LLM 服務
│
├── models/                            # 模型層，處理數據操作和邏輯
│   ├── document_model.py              # 文件模型
│   ├── llm_model.py                   # LLM 模型
│
├── apis/                              # API 層，負責與外部服務進行交互
│   ├── llm_api.py                     # LLM API
│   ├── embedding_api.py               # 嵌入 API
│   ├── file_paths.py                  # 文件路徑和數據儲存處理
│
├── data/                              # 數據文件夾，包含臨時和持久化的數據存儲
│   ├── tmp/                           # 臨時文件存儲目錄
│   ├── vector_store/                  # 本地向量數據庫存儲目錄
│   ├── output/                        # 輸出文件存儲目錄



## View（視圖層）
- app.py: 主應用程序文件，負責配置頁面和初始化控制器，啟動應用程式。

## Controller（控制器層）
- ui_controller.py: UI 控制器，負責處理來自視圖層的請求，調用服務層來執行業務邏輯，並將結果返回給視圖層。
- 
## Services（服務層）
服務層負責處理業務邏輯，與模型層交互，並將結果返回給控制器層。
- document_services.py: 文件服務，負責處理文件的加載、拆分、嵌入等操作的業務邏輯。
- llm_services.py: LLM 服務，負責處理LLM查詢邏輯，調用LLM模型以獲取答案。

## Model（模型層）
模型層負責數據操作和邏輯，包括數據的存取、處理和持久化。
- document_model.py: 文件模型，負責處理文件的加載、拆分和嵌入等操作。
- llm_model.py: LLM 模型，負責與LLM API的交互並處理查詢邏輯。

## APIs（API 層）
- llm_api.py: LLM API，負責調用外部LLM服務
- embedding_api.py: 嵌入 API，負責調用嵌入生成服務。 
- file_paths.py: 文件路徑和數據儲存處理，提供統一的文件路徑管理。

## data（數據文件夾）
- tmp: 臨時文件存儲目錄，用於存儲臨時數據文件。
- vector_store: 本地向量數據庫存儲目錄，用於存儲向量數據庫文件。
- output: 輸出文件存儲目錄，用於存儲輸出的結果文件。