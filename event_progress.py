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

# === 3. 將資料按日期排序並分成5段 ===
articles = sorted(articles.items(), key=lambda x: x[0])
total = len(articles)
chunk_size = total // 5 + (1 if total % 5 else 0)  # 確保可被5段涵蓋

for i in range(5):
    chunk = articles[i * chunk_size:(i + 1) * chunk_size]
    if not chunk:
        continue  # 跳過空段落

    news_content = ""
    urls = []

    for date, daily_articles in chunk:
        for a in daily_articles:
            title = a.get("Title", "")
            content = a.get("Content", "")
            url = a.get("URL", "")
            urls.append(url)
            news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n日期:{date}\n---\n"

    prompt = f"""
    請閱讀以下多篇新聞，並完成以下任務：

    1. 統整此時段新聞進展：
    - 這些新聞依時間排序，請分析此段時間的整體事件發展、趨勢與關鍵轉折。
    - 請根據新聞內容整理主要事件的演變與變化。
    
    2. 摘要與脈絡分析：
    - Summary 最多 15 個字，簡潔描述此時段的關鍵進展。
    - 請補充此段期間的事件脈絡、原因與結果關係。

    3. 回覆格式為 JSON（請嚴格遵守）：
    {{
        "Part": "{i + 1}",
        "DateRange": "{chunk[0][0]} ~ {chunk[-1][0]}",
        "Summary": "請填入簡要摘要（15字內）",
        "URL": {json.dumps(urls, ensure_ascii=False)}
    }}

    注意事項：
    - 嚴格遵守 JSON 格式，並確保格式正確。
    - 不要有 JSON 以外的文字或說明。
    - Summary 最多15個字，請簡潔明瞭。
    - 所有內容使用繁體中文。
    以下是新聞資料：
    {news_content}
    """

    res = model.generate_content(prompt)
    clean_text = res.text.replace("```json", "").replace("```", "").strip()
    
    output_file_path = os.path.join(output_folder, f"translate_progress_part_{i + 1}.json")
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    print(f"第 {i + 1} 區段 已處理完畢，儲存至 {output_file_path}")


    # # 根據日期給輸出檔名
    # output_file_path = os.path.join(output_folder, f"progress_{date.replace('/', '-')}.json")
    # clean_text = res.text.replace("```json", "").replace("```", "").strip()
    # clean_text = res.text.replace("```json", "").replace("```", "").strip()
    # with open(output_file_path, "w", encoding="utf-8") as f:
    #     f.write(clean_text)
    # print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    