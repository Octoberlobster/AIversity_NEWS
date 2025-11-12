# 使用官方 playwright image（已經包含 Chromium/Firefox/Webkit）
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# 設定工作目錄
WORKDIR /app

# 安裝 Python 需求 (如果你有 requirements.txt)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir playwright==1.56.0 && \
    playwright install --with-deps
    
# 複製程式碼
COPY . .

# 執行主程式
CMD ["python3", "schedule_test.py"]