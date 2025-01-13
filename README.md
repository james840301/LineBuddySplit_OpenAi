# LineBuddySplit_OpenAi

> LineBuddySplit_OpenAi 是一個專為 分帳 設計的 LINE 機器人，專注於費用管理與分攤，同時提供直觀的互動式可視化圖表，讓分帳過程更簡單高效。

## **功能特點**

- 自動計算與分攤費用：針對群組活動費用，自動計算分攤金額，避免手動計算的麻煩。
- 互動式圖表：使用柱狀圖、圓餅圖和流程圖，展示費用分佈與轉帳方案，提供清晰的視覺化數據。
- 智能互動：集成 OpenAI API，實現自然語言處理功能，讓用戶能以更自然的方式與機器人互動。
- 自我喚醒機制：防止應用在免費部署平台上進入休眠，保持穩定運行。
- 高可靠性：通過單元測試確保程式模組穩定性，降低運行中錯誤的風險。
- 持續集成與交付（CI/CD）：使用 GitHub Actions 自動化測試、打包並部署應用。

## **使用技術**

- **後端**：Python, Flask  
- **訊息處理**：LINE Messaging API  
- **自然語言處理**：整合 OpenAI API，為分帳功能提供更智能的語意解析與回應。  
- **資料視覺化**：使用 Plotly 生成互動式圖表，展示費用分佈與轉帳方案。  
- **部署與基礎設施**：  
  - **AWS Lambda**：運行後端應用的無伺服器架構，確保高效且成本效益的運行。  
  - **AWS ECR（Elastic Container Registry）**：用於管理和部署 Docker 容器，確保應用能夠快速部署並與 Lambda 集成。  
- **容器化**：使用 Docker 打包應用，確保一致的運行環境，方便部署與維護。  
- **測試**：採用單元測試框架（如 `unittest` 或 `pytest`）進行程式測試，提升代碼可靠性。  
- **持續集成與交付（CI/CD）**：基於 GitHub Actions 實現以下流程：  
  - 自動化單元測試。  
  - Docker 容器構建並推送至 AWS ECR。  
  - 部署至 AWS Lambda。  
- **環境管理**：dotenv 用於安全管理環境變數。  

---

## **安裝指南**

1. **複製專案代碼**：
   ```bash
   git clone https://github.com/your-username/LineBuddySplit_OpenAi.git
   cd LineBuddySplit_OpenAi

2. **建立虛擬環境**：
    ```bash
   python -m venv venv
   source venv/bin/activate   # 對於 macOS/Linux
   venv\Scripts\activate      # 對於 Windows

3. **安裝所需套件**：
    ```bash
    pip install -r requirements.txt

4. **設定環境變數**：在專案根目錄下建立 .env 文件，並填入以下內容：
    ```
    在專案根目錄下建立 .env 文件，並填入以下內容：
    LINE_CHANNEL_ACCESS_TOKEN=你的LINE頻道存取金鑰
    LINE_CHANNEL_SECRET=你的LINE頻道密鑰
    OPENAI_API_KEY=你的OpenAI API密鑰
    BASE_URL=你的應用網址 (例如：https://your-app-url.onrender.com)
    ```

5. **運行應用程式**：
    ```bash
    python app.py

6. **公開應用（本地測試時）**：
    使用 ngrok 或類似工具：
    ```bash
    ngrok http 5000

## **使用方法**

1. **將機器人加入 LINE**：
- 將機器人邀請至你的 LINE 私人聊天。

2. **開始使用機器人**：
- 輸入成員列表（例如：Alice、Bob、Charlie）。
- 輸入付款記錄（例如：Alice付了100元晚餐）。
- 輸入分攤規則（例如：晚餐沒Bob、Charlie）。

3. **獲取結果**：
- 機器人會計算並顯示最終餘額。
- 同時會提供可視化圖表的連結。

## **專案結構**
```
   LineBuddySplit_OpenAi/
   ├── app.py                     # 主應用程式
   ├── expense_chart_generator.py # 圖表生成邏輯
   ├── message_processor.py       # 分攤費用邏輯
   ├── user_message_handler.py    # LINE 事件處理
   ├── test/                      # 單元測試
   ├── requirements.txt           # 套件需求
   ├── .env                       # 環境變數 (不會被提交到 Git)
   ├── README.md                  # 專案說明文件
```
## **部署指南**
1. **部署至 AWS Lambda：**：
- 構建 Docker 容器：將應用程式打包為 Docker 映像。
- 推送至 AWS ECR：將 Docker 映像推送至 AWS Elastic Container Registry。
- 更新 Lambda 配置：將 Lambda 配置更新為新的容器映像。
2. **更新 BASE_URL**：
- 部署完成後，將 .env 文件中的 BASE_URL 更新為您的 AWS Lambda 應用網址。

## **CI/CD 自動化流程**
- 本專案已設置 GitHub Actions，支援自動化測試、Docker 容器構建、推送至 AWS ECR 並部署至 AWS Lambda。
- 流程包含：
  - 1.單元測試：每次提交代碼會自動執行測試，確保應用程式穩定性。
  - 2.容器化構建：使用 Docker 構建應用容器。
  - 3.自動部署：將應用容器推送至 AWS ECR 並更新至 AWS Lambda。
    
