<<<<<<< Updated upstream
﻿import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# === 1. 設定本機檔案路徑 ===
input_file_path = "Graduation-Project\\json\\2025_02_24_00\\台灣新聞_2025_02_24_00.json"
output_file_path = "台灣新聞_cleaned.json"

# === 2. 設定/取得 Gemini API 金鑰 ===
# 方法一：從環境變數取得（建議在 OS 或 CI/CD 設置環境變數 GEMINI_API_KEY）
api_key = "AIzaSyCuoZsWCGbYgHlpEOaK8f9krSXXH74h0Uw"

# 方法二：直接在程式中手動設定 （範例）
# api_key = "YOUR_GEMINI_API_KEY"

# 如果沒有設定 api_key，可以在這裡進行檢查
if not api_key:
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 3. 讀取 JSON 檔案 ===
with open(input_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === 4. 處理每篇新聞內容 ===
for article in data:
    # (1) 去除 HTML
    soup = BeautifulSoup(article["Content"], "html.parser")
    cleaned_text = soup.get_text(separator="\n", strip=True)

    # (2) 使用 Gemini API 去除雜訊
    prompt = f"""
    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

    {cleaned_text}
    """
    response = model.generate_content(prompt)
    article["Content"] = response.text  # 更新文章內容

# === 5. 輸出處理後的結果到 JSON 檔案 ===
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ 處理完成！純文字新聞已儲存至 {output_file_path}")
=======
﻿import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# === 1. 設定本機檔案路徑 ===
input_file_path = "Graduation-Project\\json\\2025_02_24_00\\台灣新聞_2025_02_24_00.json"
output_file_path = "台灣新聞_cleaned.json"

# === 2. 設定/取得 Gemini API 金鑰 ===
# 方法一：從環境變數取得（建議在 OS 或 CI/CD 設置環境變數 GEMINI_API_KEY）
api_key = "AIzaSyDRNysvX5bd8Xk92zS0Dh6VEkYyv1SgJ5s"

# 方法二：直接在程式中手動設定 （範例）
# api_key = "YOUR_GEMINI_API_KEY"

# 如果沒有設定 api_key，可以在這裡進行檢查
if not api_key:
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 3. 讀取 JSON 檔案 ===
with open(input_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === 4. 處理每篇新聞內容 ===
for article in data:
    # (1) 去除 HTML
    soup = BeautifulSoup(article["Content"], "html.parser")
    cleaned_text = soup.get_text(separator="\n", strip=True)

    # (2) 使用 Gemini API 去除雜訊
    prompt = f"""
    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

    {cleaned_text}
    """
    response = model.generate_content(prompt)
    article["Content"] = response.text  # 更新文章內容

# === 5. 輸出處理後的結果到 JSON 檔案 ===
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ 處理完成！純文字新聞已儲存至 {output_file_path}")
>>>>>>> Stashed changes
