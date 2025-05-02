import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
import time

# === 1. 設定資料夾路徑 ===
input_folder = "json"
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# === 2. 設定 Gemini API 金鑰 ===
api_key = ""

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"cleaned2_{filename}")

        # 讀取 JSON 檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 處理每篇新聞內容
        for article in data:
            if "Content" in article:
                # (1) 去除 HTML
                soup = BeautifulSoup(article["Content"], "html.parser")
                cleaned_text = soup.get_text(separator="\n", strip=True)

                # (2) 使用 Gemini API 提取發布時間
                taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
                formatted_time = time.strftime("%Y/%m/%d", taiwan_time)
                response2 = model.generate_content(
                    cleaned_text + " 根據以上新聞摘要，請提取發布時間，如有更新時間，請提取更新時間，格式為 yyyy/MM/dd，若僅有hours ago，則用" + formatted_time + "。" +
                    "如果沒有時間，請回覆「無法提取發布時間」" +
                    "如果只有 月/日，請在前面加上當前年份" +
                    "無需任何其他說明或標題。"
                )
                article["PublishTime"] = response2.text.strip()  # 更新文章發布時間

                # (2) 使用 Gemini API 去除雜訊
                prompt = f"""
                請幫我從網頁內容中提取新聞標題：

                {cleaned_text}

                你只需要回覆標題，忽略廣告與無關內容，不需要任何其他說明或標題。
                """
                response = model.generate_content(prompt)
                article["Title"] = response.text.strip()  # 更新文章 title

                # # (2) 使用 Gemini API 去除雜訊
                prompt = f"""
                請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                {cleaned_text}

                你只需要回覆經過處理的內容，不需要任何其他說明或標題。
                """
                response = model.generate_content(prompt)
                article["Content"] = response.text.strip()  # 更新文章內容

                # # (2) 使用 Gemini API 去除雜訊
                prompt = f"""
                請幫我提取新聞來自哪個媒體：

                {cleaned_text}

                你只需要回覆媒體名稱，如果找不到，就生成不知。
                """
                response = model.generate_content(prompt)
                article["Source"] = response.text.strip()  # 更新文章來源

        # 輸出處理後的結果到新 JSON 檔案
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ {filename} 處理完成！已儲存至 {output_file_path}")

print("🎉 所有 JSON 檔案處理完成！")