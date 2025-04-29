import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep
from supabase import create_client, Client
import uuid
import datetime

url = "supabase.co那個東東"
key = "supabase的key"
supabase: Client = create_client(url, key)
response = supabase.table('cleaned_news').select("*").execute()
# print(response.data)
dates = [row['date'] for row in response.data]
titles = [row['title'] for row in response.data]
contents = [row['content'] for row in response.data]
urls = [row['url'] for row in response.data]
# print(dates)

# 存輸出的
output_folder = "json/processed"
os.makedirs(output_folder, exist_ok=True)

api_key = "我終於記得刪了"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

articles = {}
for row in response.data:
    date = row["date"]
    # date留下來的格式是2023-10-01取前10個字元
    date = date[:10]
    if date not in articles:
        articles[date] = []
    articles[date].append({"title" : row["title"],"content" : row["content"],"url" : row["url"], "sourcecle_media" : row["sourcecle_media"]})

# 按日期排序分成5段
articles = sorted(articles.items(), key=lambda x: x[0])
total = len(articles)
chunk_size = total // 5 + (1 if total % 5 else 0)  # 確保可被5段涵蓋

for i in range(5):
    chunk = articles[i * chunk_size:(i + 1) * chunk_size]
    if not chunk:
        continue  # 跳過空段落

    news_content = ""
    urls = []
    sources = []

    for date, daily_articles in chunk:
        for a in daily_articles:
            title = a.get("title", "")
            content = a.get("content", "")
            url = a.get("url", "")
            urls.append(url)
            source = a.get("sourcecle_media", "")
            sources.append(source)
            news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n日期:{date}\n---\n"

    prompt = f"""
    請閱讀以下多篇新聞，並完成以下任務：

    1. 統整此時段新聞進展：
    - 這些新聞依時間排序，請分析此段時間的整體事件發展、趨勢與關鍵轉折。
    - 請根據新聞內容整理主要事件的演變與變化。
    
    2. 摘要與脈絡分析：
    - Summary 最多 15 個字，簡潔描述此時段的關鍵進展。
    - 請補充此段期間的事件脈絡、原因與結果關係。

    3. 回覆格式為 JSON，請參考以下結構（請嚴格遵守）：
    {{
        "Part": "{i + 1}",
        "DateRange": "{chunk[0][0]} ~ {chunk[-1][0]}",
        "Summary": "請填入簡要摘要（15字內）",
        "URL": {json.dumps(urls, ensure_ascii=False)},
        "Source": {json.dumps(sources, ensure_ascii=False)},
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
    print(f"第 {i + 1} 區段的回覆：\n{clean_text}\n")
    # 把結果轉回 dict
    try:
        result = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"錯誤", e)
        continue

    # 自動生成一個 UUID 作為 id
    item_id = str(uuid.uuid4())

    # 拿出日期範圍的開始日
    date_range = result.get("DateRange", "")
    start_date = date_range.split("~")[0].strip() if "~" in date_range else ""

    # 寫入資料庫
    timeline_items_insert_data = {
        "timeline_items_id": item_id,
        "date_range": date_range,
        "start_date": start_date,
        "summary": result.get("Summary", "")
    }
    print(timeline_items_insert_data)


    sources = result.get("Source", [])
    urls = result.get("URL", [])
    for source, url in zip(sources, urls):
        timeline_sources_id = str(uuid.uuid4())
        insert_data = {
            "timeline_sources_id" : timeline_sources_id,
            "timeline_items_id": item_id,  # FK 連 timeline_items.id
            "source": source,
            "url": url
        }
        print(insert_data)
        # response = supabase.table("timeline_sources").insert(insert_data).execute()
        # if response.error:
        #     print(f"timeline_sources insert 失敗：{response.error}")


    # response = supabase.table("timeline_items").insert(insert_data).execute()
    # if response.error:
    #     print(f"timeline_items insert 失敗：{response.error}")