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
        
for date, daily_articles in articles:
    news_content = ""
    for a in daily_articles:
        title = a.get("Title", "")
        url = a.get("URL", "")
        content_raw = a.get("Content", "")
        content = BeautifulSoup(content_raw, "html.parser").get_text().strip()

        news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n---\n"
    # print(news_content)
    
    prompt = f"""
    你是一位新聞分析專家，請仔細閱讀以下多篇新聞內容，並完成以下任務：
    
    1. 這些新聞都來自同一天，請依照不同新聞台的報導內容，找出報導內容相似的新聞台
    2. 為這些相近報導內容給予一個簡短的摘要（最多15字），並列出這些新聞台的名稱
    3. 請將這些新聞台的名稱與摘要整理成 JSON 格式，並確保格式正確。

    請依照以下 JSON 格式回答：
    [
        {{
            "Topic": "內容相近新聞之摘要（最多15字）",
            "News_sources": ["新聞台1", "新聞台2", "新聞台3"],
        }},
        ...
    ]
    注意：
    - 內容都使用繁體中文。

    以下是新聞資料：
    {news_content}
    """

    res = model.generate_content(prompt)

    # 根據日期給輸出檔名    
    date_filename = date.replace("/", "-")
    output_file_path = os.path.join(output_folder, f"similarty_{date_filename}.json")
    clean_text = res.text.replace("```json", "").replace("```", "").strip()
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    print(f"{date} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    