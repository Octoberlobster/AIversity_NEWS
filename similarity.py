from collections import defaultdict
import uuid, json, os
from bs4 import BeautifulSoup
from time import sleep
import google.generativeai as genai
from supabase import create_client
from supabase import Client
import re
from datetime import datetime

SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
GEMINI_API_KEY       = os.getenv("API_KEY_Ge")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-002')


def parse_date_range(dr: str):
    """
    gemini會亂回格式
    """
    if not dr:
        return None, None
    dr = re.sub(r'\s', '', dr).replace("～", "~")# 去空白、全形 ~
    if "~" in dr:
        d1, d2 = dr.split("~", 1)
    else:
        d1 = d2 = dr
    def fix(s):
        return datetime.strptime(s, "%Y%m%d").strftime("%Y-%m-%d") if len(s) == 8 else s
    return fix(d1), fix(d2)


def similarity(articles: list[dict], date_range: str):
    articles.sort(key=lambda x: x["date"])
    news_txt = ""
    for art in articles:
        body = BeautifulSoup(art["content"], "html.parser").get_text(" ", strip=True)
        news_txt += (
            f"標題：{art['title']}\n內容：{body}\n連結：{art['url']}\n日期：{art['date']}\n---\n"
        )
    prompt = f"""
你是一位新聞分析專家，請仔細閱讀以下多篇新聞內容，並完成以下任務：

1. 這些新聞屬於同一段時間，請找出報導內容相近的新聞群組（若只有一群，就輸出一群）。
2. 為每個群組提供一個最多 15 字的摘要，並列出此群組包含的新聞台。
3. 嚴格使用 JSON，內容範例如下（DateRange 已替你填好）：

[
  {{
    "DateRange": "{date_range}",
    "Topic": "內容相近新聞之摘要（最多15字）",
    "News_sources": ["新聞台1", "新聞台2"]
  }}
]

禁止輸出任何 JSON 以外的文字。
所有文字請用繁體中文。
以下是新聞資料：
{news_txt}
""".strip()

    for _ in range(3):
        try:
            res = model.generate_content(prompt)
            txt = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(txt)
        except Exception:
            sleep(1)
    return []

events_news = defaultdict(list)
resp = (
    supabase.table("event_original_map")
    .select("event_id, cleaned_news(title, content, url, sourcecle_media, date)")
    .execute()
).data

for row in resp:
    eid, lst = row["event_id"], row.get("cleaned_news") or []
    if isinstance(lst, dict):
        lst = [lst]
    for art in lst:
        if isinstance(art, dict):
            art["date"] = art["date"][:10]
            events_news[eid].append(art)

timeline_rows = (
    supabase.table("timeline_items")
    .select("timeline_items_id, event_id, date_range")
    .execute()
).data

# 一個 timeline_item 一個 topic
for tl in timeline_rows:
    eid  = tl["event_id"]
    t_id = tl["timeline_items_id"]
    d1, d2 = parse_date_range(tl["date_range"])

    if not (d1 and d2):
        print(f"date_range又爆了")
        continue
    arts = [a for a in events_news.get(eid, []) if d1 <= a["date"] <= d2]
    if not arts:
        print(f"[{eid}] {d1} ~ {d2} 範圍內無新聞")
        continue

    date_range_str = f"{d1} ~ {d2}"
    result = similarity(arts, date_range_str)

    topic_info = result[0]
    if not topic_info.get("Topic"):
        print(f"[{eid}] {date_range_str} 沒有 Topic")
        continue

    # news_topics
    nt_id = str(uuid.uuid4())
    supabase.table("news_topics").insert({
        "news_topics_id": nt_id,
        "timeline_item_id": t_id,
        "topic": topic_info["Topic"]
    }).execute()

    # news_topic_sources
    sources = [s for s in topic_info.get("News_sources", []) if s]
    if sources:
        src_rows = [{
            "news_topic_sources_id": str(uuid.uuid4()),
            "news_topics_id": nt_id,
            "source": s
        } for s in sources]
        supabase.table("news_topic_sources").insert(src_rows).execute()

    # print(f"[{eid}] {date_range_str}: 寫入 topic 1，sources = {len(sources)}")
print("完成")