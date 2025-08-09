import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep
from supabase import create_client, Client
import uuid
import datetime
from collections import defaultdict

SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
GEMINI_API_KEY       = os.getenv("API_KEY_Ge")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-002')

response = (
    supabase.table("event_original_map")
    .select(
        "event_id,"
        "cleaned_news (title, content, url, sourcecle_media, date)"
    )
    .execute()
)
rows = response.data  # List[Dict]
print(json.dumps(rows[0], indent=2))
# print(rows[1])

# event_id分組排序
events_news: dict[uuid.UUID, list[dict]] = defaultdict(list)
for r in rows:
    eid = r["event_id"]
    news_items = r.get("cleaned_news")
    if isinstance(news_items, dict):
        news_items = [news_items]
    elif not isinstance(news_items, list):
        news_items = []

    for n in news_items:
        if isinstance(n, dict) and "date" in n:
            n["date"] = n["date"][:10]
            events_news[eid].append(n)

for eid in events_news:
    events_news[eid].sort(key=lambda x: x["date"])
# for eid in list(events_news.keys())[:3]:
#     print(f"\nEvent ID: {eid}")
#     for news in events_news[eid]:
#         print(news)

def analyse_event(eid: int, news_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    total = len(news_rows)
    if total == 0:
        return [], []

    chunk_size = total // 5 + (1 if total % 5 else 0)
    items, sources = [], []

    for idx in range(5):
        chunk = news_rows[idx * chunk_size : (idx + 1) * chunk_size]
        if not chunk:
            continue

        # 整理 prompt
        news_block, urls, srcs = "", [], []
        for art in chunk:
            news_block += (
                f"標題：{art['title']}\n"
                f"內容：{art['content']}\n"
                f"連結：{art['url']}\n"
                f"日期：{art['date']}\n---\n"
            )
            urls.append(art["url"])
            srcs.append(art["sourcecle_media"])

        date_range = f"{chunk[0]['date']} ~ {chunk[-1]['date']}"
        prompt = f"""
                請閱讀以下多篇新聞，並完成以下任務：

                1. 統整此時段新聞進展：
                - 這些新聞依時間排序，請分析此段時間的整體事件發展、趨勢與關鍵轉折。
                2. 摘要與脈絡分析：
                - Summary 最多 15 個字，簡潔描述此時段的關鍵進展。

                3. 回覆格式為 JSON（嚴格遵守）：
                {{
                "Part": "{idx + 1}",
                "DateRange": "{date_range}",
                "Summary": "請填入簡要摘要（15字內）",
                "URL": {json.dumps(urls, ensure_ascii=False)},
                "Source": {json.dumps(srcs, ensure_ascii=False)}
                }}

                注意：
                - 只能輸出 JSON。
                - Summary 最多 15 個字。
                - 使用繁體中文。

                以下是新聞資料：
                {news_block}
                """.strip()

        for retry in range(3):
            try:
                res = model.generate_content(prompt)
                raw = (
                    res.text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )
                j = json.loads(raw)
                break
            except Exception as e:
                if retry == 2:
                    print(f"{eid}{e}")
                    return [], []
                sleep(1)
        # timeline_items
        item_id = str(uuid.uuid4())
        items.append(
            {
                "timeline_items_id": item_id,
                "event_id": eid, #感覺要
                "date_range": j["DateRange"],
                "start_date": j["DateRange"].split("~")[0].strip(),
                "summary": j["Summary"],
            }
        )
        # timeline_sources
        for s, u in zip(j["Source"], j["URL"]):
            sources.append(
                {
                    "timeline_sources_id": str(uuid.uuid4()),
                    "timeline_items_id": item_id,
                    "source": s,
                    "url": u,
                }
            )

    return items, sources

for eid, news in events_news.items():
    print(f"處理事件 {eid}")
    items_rows, sources_rows = analyse_event(eid, news)
    print(items_rows)
    print(sources_rows)
    #supabase.table("timeline_items").insert(items_rows).execute()
    #supabase.table("timeline_sources").insert(sources_rows).execute()
    print(f"完成插入items {len(items_rows)}、sources {len(sources_rows)}")