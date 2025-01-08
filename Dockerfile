# 使用 AWS 官方的 Lambda Python 3.13 基底映像檔
FROM public.ecr.aws/lambda/python:3.13

# 設定工作目錄
WORKDIR /app

# 複製需求檔案並安裝依賴
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式的檔案和資料夾
COPY app ./app
COPY user_message_handler ./
COPY expense_chart_generator ./
COPY message_processor ./
COPY separate_charts ./
COPY static ./static
COPY rule ./rule

# 設定 Docker 容器啟動時執行的命令
CMD ["app.lambda_handler"]
