import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep
# 總結15字，日期，(連結保留)

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

api_key = "AIzaSyAcS3oO-4niAZKUlULc03dQzbmSTQjkFH8"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 2. 處理資料夾內所有檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)

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

for date, daily_articles in articles:
    news_content = ""
    urls = []
    for a in daily_articles:
        title = a.get("Title", "")
        content = a.get("Content", "")
        url = a.get("URL", "")
        urls.append(url)
        news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n---\n"
    # print(news_content)
    
    prompt = f"""
        請仔細閱讀以下多篇新聞內容，並完成以下任務：

        1. 依日期整理每日進展：
        - 這些都是同一天的新聞報導且都關於同一件主要事件，請根據每篇新聞所提供的資訊，整理該事件當天的重要發展與關鍵資訊。
        - 如找不到明確日期，請使用報導發布日期或以 "不明" 標註。

        2. 摘要與脈絡分析：
        - Summary最多15個字，請簡潔明瞭。
        - 完成每日進展後，請為整個事件做簡要的總結與脈絡說明，例如整體演變、關鍵轉折點，最多15個字。

        3. 請使用以下 JSON 格式回覆（請嚴格遵守，不要附加多餘文字）：
        {{
        "Date": "{date}",
        "Summary": "當天發生了什麼事情的簡要描述",
        "URL": {json.dumps(urls, ensure_ascii=False)}
        }}
                                     
        注意：
        - Summary最多15個字，請簡潔明瞭。
        - 內容都使用繁體中文。
        以下是新聞資料：
        {news_content}
        """
    res = model.generate_content(prompt)

    # 根據日期給輸出檔名
    output_file_path = os.path.join(output_folder, f"progress_{date.replace('/', '-')}.json")
    clean_text = res.text.replace("```json", "").replace("```", "").strip()
    clean_text = res.text.replace("```json", "").replace("```", "").strip()
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    