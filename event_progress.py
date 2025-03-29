import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

api_key = "AIzaSyDwNOkobaknphQQx8NqSVZ6bDSvW_pizlg"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 2. 處理資料夾內所有檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"cleaned_{filename}")

        # 讀txt檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # 根據分隔線切割成多篇新聞
        articles = [a.strip() for a in raw_text.split('--------------------------------------------------') if a.strip()]
        
        # 組合成資料給 Gemini
        combined_data = ""
        for idx, article in enumerate(articles, start=1):
            combined_data += f"[{idx}]\n{article}\n\n"
        print(combined_data [:500])

        # 組合 Prompt
        res = model.generate_content( """
        請根據以下多則新聞摘要，整理出每個事件的每日進展情況。請先根據事件主題將新聞分群，再依照日期整理事件的發展過程。

        請用以下 JSON 格式回覆：
        {
        "事件名稱1（請你幫忙取名）": {
            "進展": [
            {
                "日期": "YYYY-MM-DD",
                "摘要": "當天發生了什麼事情的簡要描述",
                "關鍵字": ["keyword1", "keyword2"],
                "相關新聞索引": [1, 2], 
                "來源網址": ["url1", "url2"]
            },
            {
                "日期": "YYYY-MM-DD",
                "摘要": "...",
                "關鍵字": ["..."],
                "相關新聞索引": [3],
                "來源網址": ["url3"]
            }
            ]
        },
        "事件名稱2": {
            "進展": [ ... ]
        }
        }

        以下是新聞資料：
        
        """ + combined_data)

        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(res.text)
        print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    