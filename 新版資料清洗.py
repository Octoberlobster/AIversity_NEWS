import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# === 1. 設定資料夾路徑 ===
input_folder = "Graduation-Project/json/2025_02_24_00"
output_folder = "Graduation-Project/json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# === 2. 設定 Gemini API 金鑰 ===
api_key = "API_KEY"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"cleaned_{filename}")

        # 讀取 JSON 檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 處理每篇新聞內容
        for article in data:
            if "Content" in article:
                # (1) 去除 HTML
                soup = BeautifulSoup(article["Content"], "html.parser")
                cleaned_text = soup.get_text(separator="\n", strip=True)

                # (2) 使用 Gemini API 去除雜訊
                prompt = f"""
                請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                {cleaned_text}
                """
                response = model.generate_content(prompt)
                article["Content"] = response.text.strip()  # 更新文章內容

        # 輸出處理後的結果到新 JSON 檔案
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ {filename} 處理完成！已儲存至 {output_file_path}")

print("🎉 所有 JSON 檔案處理完成！")
