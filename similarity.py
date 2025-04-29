import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep
# 先把新聞時間整理好，把同一天的新聞整理在一起，然後用同一天的新聞去比對相似度，

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

api_key = "AIzaSyBPIEu1pz4ykfRnCBcMNXfWdXdCzDwTuDI"

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
# === 3. 整理新聞，按日期排序後分為五段 ===
articles = sorted(articles.items(), key=lambda x: x[0])
total = len(articles)
chunk_size = total // 5 + (1 if total % 5 else 0)

for i in range(5):
    chunk = articles[i * chunk_size:(i + 1) * chunk_size]
    if not chunk:
        continue

    news_content = ""
    date_range = f"{chunk[0][0]} ~ {chunk[-1][0]}"

    for date, daily_articles in chunk:
        for a in daily_articles:
            title = a.get("Title", "")
            url = a.get("URL", "")
            content_raw = a.get("Content", "")
            content = BeautifulSoup(content_raw, "html.parser").get_text().strip()
            news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n日期:{date}\n---\n"

    prompt = f"""
    你是一位新聞分析專家，請仔細閱讀以下多篇新聞內容，並完成以下任務：

    1. 這些新聞來自不同日期，但屬於同一段時間，請找出報導內容相近的新聞群組。
    2. 為每個內容相似的群組，提供一個簡短的摘要（最多15字），並列出這些新聞來源的新聞台。
    3. 若不同新聞台重複報導相似內容，請合併並歸為同一群組。

    請依照以下 JSON 格式回答：
    [
        {{
            "DateRange": "{date_range}",
            "Topic": "內容相近新聞之摘要（最多15字）",
            "News_sources": ["新聞台1", "新聞台2", "新聞台3"]
        }},
        ...
    ]

    注意：
    - 嚴格遵守 JSON 格式，並確保格式正確。
    - 不要有 JSON 以外的文字或說明。
    - 所有內容使用繁體中文。
    - 日期範圍請使用給定的 dateRange。
    以下是新聞資料：
    {news_content}
    """

    res = model.generate_content(prompt)
    clean_text = res.text.replace("```json", "").replace("```", "").strip()

    output_file_path = os.path.join(output_folder, f"translate_similarty_part_{i + 1}.json")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(clean_text)
    print(f"第 {i + 1} 區段相似新聞分析完成，儲存至 {output_file_path}")

print("所有檔案處理完成！")