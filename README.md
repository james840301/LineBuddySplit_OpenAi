# LineBuddySplit

> 一個專為分帳的 LINE 機器人，用於管理和分攤費用，並提供互動式可視化圖表。

## **功能特點**

- 自動計算和分攤群組活動費用。
- 提供互動式圖表（柱狀圖、圓餅圖、流程圖）來展示費用分佈與轉帳方案。
- 自我喚醒機制，防止應用在免費部署平台上進入休眠。

## **使用技術**

- **Backend**: Python, Flask
- **Messaging**: LINE Messaging API
- **Visualization**: Plotly
- **Deployment**: Render
- **Environment Management**: dotenv

---

## **安裝指南**

1. **複製專案代碼**：
   ```bash
   git clone https://github.com/your-username/LineBuddySplit.git
   cd LineBuddySplit

2. **建立虛擬環境**：
    ```bash
    python -m venv venv
    source venv/bin/activate   # 對於 macOS/Linux
    venv\Scripts\activate      # 對於 Windows

3. **安裝所需套件**：
    ```bash
    pip install -r requirements.txt

4. **設定環境變數**：
    ```
    在專案根目錄下建立 .env 文件，並填入以下內容：
    LINE_CHANNEL_ACCESS_TOKEN=你的LINE頻道存取金鑰
    LINE_CHANNEL_SECRET=你的LINE頻道密鑰
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
    LineBuddySplit/
    ├── app.py                     # 主應用程式
    ├── expense_chart_generator.py # 圖表生成邏輯
    ├── message_processor.py       # 分攤費用邏輯
    ├── user_message_handler.py    # LINE 事件處理
    ├── test/                      # 單元測試
    ├── requirements.txt           # 套件需求
    ├── .env                       # 環境變數 (不會被提交到 Git)
    ├── README.md                  # 專案說明文件

## **部署指南**
1. **部署至 Render**：
- 將代碼推送到 GitHub。
- 連接 Render 並創建新服務，將儲存庫部署至 Render。
- 在 Render 的「環境變數」設定中配置 .env 文件中的內容。
2. **更新 BASE_URL**：
- 在 .env 文件中將 BASE_URL 更新為你的 Render 應用網址。
    