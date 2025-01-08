from flask import Flask, request, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
from user_message_handler import MessageHandler
import threading
import time
import requests
from aws_lambda_wsgi import response


# 載入環境變數，從 .env 檔案中讀取設定
load_dotenv()

# 初始化 Flask 應用
app = Flask(__name__)

# 設定靜態檔案儲存位置，用於存放生成的圖表
STATIC_DIR = os.path.join(os.getcwd(), "static", "charts")
os.makedirs(STATIC_DIR, exist_ok=True)  # 確保資料夾存在

# 初始化 LINE Bot API 和 Webhook Handler
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")  # BASE_URL 可動態從環境變數讀取
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))  # LINE Bot API 金鑰
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))  # LINE Webhook 密鑰

# 初始化 MessageHandler
user_context = {}  # 用於儲存每個使用者的上下文資料
response_handler = MessageHandler(line_bot_api, user_context)  # 負責處理訊息邏輯

@app.route('/')
def index():
    """提供基本的歡迎頁面"""
    return "Welcome to LineBuddySplit! Your app is up and running."

@app.route("/callback", methods=["POST"])
def callback():
    """
    處理來自 LINE 的 Webhook 請求。
    每當使用者向機器人發送訊息，LINE 伺服器會將請求傳至此端點。
    """
    signature = request.headers.get("X-Line-Signature", "")  # 獲取請求頭中的簽名
    body = request.get_data(as_text=True)  # 獲取請求的主要內容
    try:
        handler.handle(body, signature)  # 處理請求內容
    except InvalidSignatureError:
        return "Invalid signature", 400  # 如果簽名驗證失敗，返回錯誤代碼
    return "OK", 200  # 成功處理後返回 200 狀態碼

@handler.add(MessageEvent, message=TextMessage)
def handle_line_message(event):
    """
    處理來自 LINE 的文字訊息事件。
    使用 MessageHandler 負責具體的業務邏輯。
    """
    response_handler.handle_message(event)

@app.route('/chart/<filename>')
def serve_chart(filename):
    """
    提供靜態圖表文件的路由。
    用戶可以通過此端點訪問生成的圖表。
    """
    return send_from_directory(STATIC_DIR, filename, mimetype='text/html')

# 新增 Lambda 入口點
def lambda_handler(event, context):
    """
    Lambda 的入口函數，使用 AWS WSGI 適配器將事件轉換為 WSGI 格式。
    """
    return response(app, event, context)

## AWS不需要喚醒功能
# @app.route('/ping')
# def ping():
#     """
#     提供健康檢查的端點。
#     可用於測試伺服器是否正常運行。
#     """
#     print("Ping endpoint was hit!")  # 日誌，用於確認是否有成功觸發
#     return "pong", 200

# def keep_awake():
#     """
#     定時向應用自身發送請求，防止應用進入休眠狀態。
#     適用於某些平台（例如 Render）在長時間無請求時可能停止運行的情況。
#     """
#     while True:
#         try:
#             response = requests.get(f"{BASE_URL}/ping", timeout=10)  # 發送 GET 請求至 /ping
#             print(f"Sent keep-alive ping to {BASE_URL}/ping - Response: {response.status_code}")  # 紀錄響應狀態碼
#         except Exception as e:
#             print("Error sending keep-alive ping:", e)  # 紀錄錯誤資訊
#         time.sleep(600)  # 每 10 分鐘發送一次

if __name__ == "__main__":
    # # 啟動喚醒功能於單獨線程
    # threading.Thread(target=keep_awake, daemon=True).start()
    # 啟動 Flask 應用
    app.run(debug=True, port=5000)
