import os
from dotenv import load_dotenv

# 確定載入和 .py 檔案同目錄的 .env 檔案
load_dotenv()

# 印出讀取到的變數值
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print(f"Supabase URL: {url}")
print(f"Supabase Key: {key}")
print(f"Gemini Key: {gemini_key}")

if not url:
    print("\n錯誤：讀取不到 SUPABASE_URL，請檢查 .env 檔案是否存在、位置是否正確、變數名稱是否無誤。")
