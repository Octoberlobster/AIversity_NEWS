import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep
# 先把新聞時間整理好，把同一天的新聞整理在一起，然後用同一天的新聞去比對相似度，
# 

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/processed"

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
        output_file_path = os.path.join(output_folder, f"similarty_{filename}")

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
        # print(articles)
        
for article in articles:
    res = model.generate_content("""
    你是一位新聞分析專家，請根據以下新聞資料進行分析。這些新聞都來自同一天，請依照不同新聞台的報導內容，找出主題相似的新聞台，並為這些相近主題寫一句簡短摘要。

    請依照以下 JSON 格式回答：
    [
    {
        "topic": "以色列與哈瑪斯衝突升級",
        "news_sources": ["TVBS", "中天", "ETtoday"]
    },
    {
        "topic": "台股今日大漲",
        "news_sources": ["聯合報", "工商時報"]
    }
    ]

    輸入資料如下：
    """ + str(article)
    )

    # 根據日期給輸出檔名
    date = article[0]
    date = date.replace("/", "-")
    print(date)
    output_file_path = os.path.join(output_folder, f"similarty_{date}.json")
    clean_text = res.text.replace("```json", "").replace("```", "").strip()
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    