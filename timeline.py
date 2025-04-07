import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/TimeLine"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

api_key = "YOUR_GEMINI_API_KEY"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 2. 處理資料夾內所有檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        # output_file_path = os.path.join(output_folder, f"progress_{filename}")

        # 讀json檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # print(data)
        
        articles = {}
        for article in data:
            date = article["date"]
            if date not in articles:
                articles[date] = []
            articles[date].append(article)

articles = sorted(articles.items(), key=lambda x: x[0])
# print(articles[0])
for article in articles:
    res = model.generate_content( """
        請仔細閱讀以下多篇新聞內容，並完成以下任務：

        1. 依日期整理每日進展：
        - 這些新聞都關於同一件主要事件，請根據每篇新聞所提供的資訊，按照新聞報導的日期（或事件發生日期）先後順序，逐日整理該事件的重要發展與關鍵資訊。
        - 若同一天內有多篇相關報導，請合併整理在同日的進展摘要中。
        - 如找不到明確日期，請使用報導發布日期或以 "不明" 標註。

        2. 摘要與脈絡分析：
        - 完成每日進展後，請為整個事件做簡要的總結與脈絡說明，包含整體演變、關鍵轉折點。

        3. 請使用以下 JSON 格式回覆（請嚴格遵守，不要附加多餘文字）：
        {
        "事件名稱（請你幫忙取名）": {
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
            ],
            "總結與分析": "請在此撰寫對整個事件的簡要回顧與可能後續影響"
        }
        }
                                     
        注意：
        - 相關新聞索引，請以本 Prompt 後所提供之新聞清單的編號為準。
        - 在引用新聞細節時，簡要概述即可，避免過度重複報導原文。
        以下是新聞資料：
        
        """ + str(article))
    
    # 根據日期給輸出檔名
    date = article[0]
    date = date.replace("/", "-")
    print(date)
    output_file_path = os.path.join(output_folder, f"{date}.json")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(res.text)
    print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    