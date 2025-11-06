from typing import Dict, Literal
from google.genai import types
from pydantic import BaseModel
from env import gemini_client, supabase
import uuid
import time
from postgrest.exceptions import APIError


def execute_builder_with_retry(builder, max_retries: int = 3):
    """Execute a postgrest request builder with retry on statement timeout."""
    for attempt in range(1, max_retries + 1):
        try:
            return builder.execute()
        except APIError as e:
            msg = str(e)
            if 'canceling statement due to statement timeout' in msg and attempt < max_retries:
                wait = attempt * 2
                print(f"[warn] DB statement timeout, retry {attempt}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            raise

categories = Literal[
    "Politics",
    "Taiwan News",
    "International News",
    "Science & Technology",
    "Lifestyle & Consumer",
    "Sports",
    "Entertainment",
    "Business & Finance",
    "Health & Wellness",
]

class AnalyzeItem(BaseModel):
    Category: categories
    Role: str
    Analyze: str

class ProAnalyzeResponse(BaseModel):
    analyze: list[AnalyzeItem]

category_description = {
    "Politics": "對於該國的政治有甚麼影響",
    "International News": "對於國際上有甚麼影響",
    "Science & Technology": "科學研究、太空探索、生物科技、AI、大數據、半導體、電子產品、電玩遊戲、網安等科技發展",
    "Lifestyle & Consumer": "旅遊、時尚、飲食、消費趨勢等",
    "Sports": "體育賽事、運動員動態、奧運、世界盃等",
    "Entertainment": "電影、音樂、藝人新聞、流行文化等",
    "Business & Finance": "對於台灣的經濟有什麼影響",
    "Health & Wellness": "公共衛生、醫學研究、醫療技術等",
}


def Pro_Analyze(story_id: str, categories: list[str]):
    # 主文章
    article = supabase.table("single_news").select("long").eq("story_id", story_id).execute()
    article_content = article.data[0]["long"]

    # 每個類別的 base 知識庫
    bases = {}
    for category in categories:
        try:
            builder = supabase.table("single_news") \
                .select("story_id,news_title,short,category,generated_date") \
                .eq("category", category) \
                .order("generated_date")
            response = execute_builder_with_retry(builder)
            data_rows = getattr(response, 'data', []) or []
            bases[category] = [{"news_title": item.get("news_title", ""), "short": item.get("short", "")} for item in data_rows]
        except Exception as e:
            print(f"[error] Failed to fetch base knowledge for category {category}: {e}")
            bases[category] = []

    system_instruction = f"""
    你將同時揣摩三個類別中最適合對文章進行分析的專家角色，
    請根據文章，針對三個類別分別提供分析。
    以下是你必須遵守的規則，如果違反將會受到嚴厲懲罰。

    規則：
    1. 確保回覆前經過嚴密的思考與分析。
    2. 產生的類別專家必須與文章內容和所選類別高度相關。
    3. 只能使用自己類別的知識庫。
    4. 分析時不要互相引用，不要混用知識庫。
    5. 所有回答使用繁體中文。
    6. 每個類別的分析必須符合下列要求：
       - 以該類別的專家角色進行分析
       - 精準描述對該類別的重大影響
       - 內容必須具體，總字數不超過 80 字
       - 不要提及「知識庫」、「文章內容」或「本篇新聞」等字眼
       - 請直接輸出具體影響
    7. 專家名稱必須清晰、準確，避免捏造不存在的職業名稱，產生真實且常見的專家名稱。
    8. 每位專家的分析必須獨立且不重複，在專家的名稱上也要有所區別。  
    9. 絕對不要出現人名。
    10. 職業名稱不要出現前

    類別與知識庫：
    {categories[0]}: {category_description[categories[0]]}，知識庫：{bases[categories[0]]}
    {categories[1]}: {category_description[categories[1]]}，知識庫：{bases[categories[1]]}
    {categories[2]}: {category_description[categories[2]]}，知識庫：{bases[categories[2]]}
    """

    prompt = f"請根據以下文章提供三個類別的專業分析：{article_content}"

    model_name = "gemini-2.5-flash-lite"
    pro_analyze = gemini_client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ProAnalyzeResponse,
        ),
    )

    if not pro_analyze or not getattr(pro_analyze, "parsed", None):
        print("pro_analyze.parsed 為 None，請檢查模型回傳內容：", pro_analyze)
        return {}

    return dict(pro_analyze.parsed)


all_require = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("single_news").select("story_id,who_talk,position_flag").order("generated_date", desc=True).range(start, start + batch_size - 1).execute()
    if not temp.data:
        print(len(all_require))
        break
    all_require.extend(temp.data)
    start += batch_size

# temp = supabase.table("single_news").select("story_id,who_talk,position_flag").range(0, 999).execute()
# all_require.extend(temp.data)

require = type("Result", (), {"data": all_require})  # 模擬原本 require 結構

all_data = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("pro_analyze").select("story_id").range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    all_data.extend([row["story_id"] for row in temp.data])
    start += batch_size

# # 去重
constraints = list(set(all_data))
# for item in require.data:
#     if item["story_id"] in constraints:
#         continue
#     if not item["position_flag"]:
#         story_id = item["story_id"]
#         who_talk = item["who_talk"]
#         for category in who_talk["who_talk"]:
#             result = Pro_Analyze(story_id,category)
#             supabase.table("pro_analyze").insert({"analyze_id": str(uuid.uuid4()),"story_id": story_id, "category": category, "analyze": result["pro_analyze"]}).execute()
#             print(f"Inserted pro_analyze for story_id {story_id} and category {category}")
#     else:
#         print(f"story_id {item['story_id']} already has position_flag {item['position_flag']}")
        
# print("All done.")

for idx, item in enumerate(require.data):
    if item["story_id"] in constraints:
        continue
    if item["who_talk"]:
        story_id = item["story_id"]
        who_talk = item["who_talk"]
        results = Pro_Analyze(story_id, who_talk["who_talk"])

        print(f"Index: {idx}, Story ID: {story_id}")
        if not results or "analyze" not in results:
            print(f"跳過 story_id {story_id}，Pro_Analyze 未回傳有效結果")
            continue

        #{'analyze': [AnalyzeItem(Category='Taiwan News', Role='結構工程技師', Analyze='該事故可能促使台灣重新檢視橋樑工程的安全標準與監管機制，避免類似事件發生，並提升公共工程品質。'), AnalyzeItem(Category='International News', Role='國際勞工安全專家', Analyze='事件突顯中國在基礎建設快速擴張下，可能存在勞工安全保障不足的問題，國際社會或將更關注中國工安標準。'), AnalyzeItem(Category='Business & Finance', Role='營建產業分析師', Analyze='或將促使在中國營運的台商重新評估其投資風險與供應鏈韌性，並可能影響相關產業的保險成本。')]}
        for result in results["analyze"]:
            builder = supabase.table("pro_analyze").insert({
                "analyze_id": str(uuid.uuid4()),
                "story_id": story_id,
                "category": result.Category,
                "analyze": (result.model_dump())
            })
            try:
                resp = execute_builder_with_retry(builder)
                if getattr(resp, 'error', None):
                    print(f"寫入 pro_analyze 發生錯誤: {resp.error}")
            except Exception as e:
                print(f"[error] Failed to insert pro_analyze for story_id {story_id}, category {result.Category}: {e}")
                continue
        print(f"Inserted pro_analyze for story_id {story_id} and categories {who_talk['who_talk']}")
        time.sleep(5)
        # break

