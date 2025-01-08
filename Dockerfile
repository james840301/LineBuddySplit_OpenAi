# 使用 AWS 官方的 Lambda Python 3.13 基底映像檔
FROM public.ecr.aws/lambda/python:3.13

# 設定工作目錄
WORKDIR /app

# 複製需求檔案並安裝依賴
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製 Python 檔
COPY app.py .
COPY expense_chart_generator.py .
COPY message_processor.py .
COPY user_message_handler.py .

# 複製資料夾
COPY rule ./rule
COPY static ./static

# 設定 Lambda 入口點（app.py 裡要有 lambda_handler）
CMD ["app.lambda_handler"]
