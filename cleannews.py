import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# === 1. 設定資料夾路徑 ===
input_folder = "json\2025_02_24_00\台灣新聞_2025_02_24_00.json"  # 存放新聞 JSON 檔案的資料夾
output_folder = "台灣新聞_2025_02_24_00_cleanned.json"  # 儲存處理後 JSON 檔案的資料夾

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# === 2. 設定 Gemini API 金鑰 ===
api_key = "AIzaSyB27FPpyasDrxrP1RKejXgQ2l6d9RSAXw4"
if not api_key:
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# === 3. 遞迴處理資料夾內的所有 JSON 檔案 ===
for root, _, files in os.walk(input_folder):
    for filename in files:
        if filename.endswith(".json"):  # 確保處理的是 JSON 檔案
            input_file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(root, input_folder)  # 計算相對路徑
            output_dir = os.path.join(output_folder, relative_path)  # 對應的輸出資料夾
            os.makedirs(output_dir, exist_ok=True)  # 確保輸出資料夾存在
            output_file_path = os.path.join(output_dir, filename)

            # 讀取 JSON 檔案
            with open(input_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 處理每篇新聞內容
            for article in data:
                soup = BeautifulSoup(article.get("Content", ""), "html.parser")
                cleaned_text = soup.get_text(separator="\n", strip=True)

                # 使用 Gemini API 去除雜訊
                prompt = f"""
                請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並盡可能保留的新聞內容：

                {cleaned_text}
                """
                response = model.generate_content(prompt)
                article["Content"] = response.text  # 更新文章內容

            # 輸出處理後的 JSON 檔案
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"✅ 處理完成！{filename} 已儲存至 {output_dir}")

print("🎉 所有新聞處理完成！")
