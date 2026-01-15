from typing import Dict, Literal
from google.genai import types
from pydantic import BaseModel
from env import gemini_client, supabase
import uuid

categories_literal = Literal[
    "Politics",
    "International News",
    "Science & Technology",
    "Lifestyle & Consumer",
    "Sports",
    "Entertainment",
    "Business & Finance",
    "Health & Wellness",
]


class AnalyzeItem(BaseModel):
    Category: categories_literal
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


def Pro_Analyze_Topic(topic_id: str, categories: list[str]):
    """針對整個專題進行多類別分析"""

    # 1️⃣ 取得專題內容
    topic_long = (
        supabase.table("topic")
        .select("topic_id, topic_long")
        .eq("topic_id", topic_id)
        .execute()
    )
    topic_content = topic_long.data[0]["topic_long"]

    # 2️⃣ 取得專題分支
    topic_branches = (
        supabase.table("topic_branch")
        .select("topic_branch_id, topic_id, topic_branch_title, topic_branch_content")
        .eq("topic_id", topic_id)
        .execute()
    )

    topic_branch_ids = [b["topic_branch_id"] for b in topic_branches.data]

    # 3️⃣ 分支與新聞的對應關係
    topic_branchs_news_stories_id = (
        supabase.table("topic_branch_news_map")
        .select("topic_branch_id, story_id")
        .in_("topic_branch_id", topic_branch_ids)
        .execute()
    )

    # 4️⃣ 查詢所有相關新聞內容
    story_ids = [i["story_id"] for i in topic_branchs_news_stories_id.data]
    if not story_ids:
        raise ValueError("此專題尚未關聯任何新聞。")

    stories = (
        supabase.table("single_news")
        .select("story_id, news_title, short")
        .in_("story_id", story_ids)
        .execute()
    )

    # 5️⃣ 組裝完整階層式專題資料
    topic_data = {
        "topic_id": topic_id,
        "topic_description": topic_content,
        "branches": [],
    }

    for branch in topic_branches.data:
        branch_id = branch["topic_branch_id"]
        related_news = [
            story
            for story in stories.data
            if story["story_id"]
            in [
                mapping["story_id"]
                for mapping in topic_branchs_news_stories_id.data
                if mapping["topic_branch_id"] == branch_id
            ]
        ]

        topic_data["branches"].append(
            {
                "branch_id": branch_id,
                "branch_title": branch["topic_branch_title"],
                "branch_content": branch["topic_branch_content"],
                "news": [
                    {
                        "story_id": n["story_id"],
                        "title": n["news_title"],
                        "summary": n["short"],
                    }
                    for n in related_news
                ],
            }
        )

    # 6️⃣ system_instruction（LLM 專家設定與限制）
    system_instruction = f"""
    你將同時揣摩三個類別中最適合對「專題」進行分析的專家角色，
    請根據提供的完整專題資料進行多角度分析。
    以下是必須要遵守的規則，如果違反將會受到嚴厲處罰。

    規則：
    1. 請確保回覆前經過嚴密的思考與分析。
    2. 每個專家的分析必須與其類別高度相關。
    3. 不可交叉引用其他類別的分析。
    4. 所有回答使用繁體中文。
    5. 每個類別的分析必須符合下列要求：
    - 以該類別專家的口吻撰寫
    - 精準描述該專題對該領域的重大影響
    - 字數不超過 150 字
    - 不可提及「文章」、「新聞」、「專題資料」等字眼
    - 直接描述觀察到的現象與趨勢
    - 精確根據各專題的分支事件與相關新聞進行分析
    6. 專家職稱須真實、合理（如經濟學者、國際關係分析師、科技產業顧問等）。
    7. 不要幫專家取名字。

    類別分析方向：
    {categories[0]}：{category_description[categories[0]]}
    {categories[1]}：{category_description[categories[1]]}
    {categories[2]}：{category_description[categories[2]]}
    """

    # 7️⃣ 固定的 Prompt 模板
    prompt = f"""
    以下是一個專題的完整結構資料，包含主題描述、各分支事件與分支中的相關新聞。
    請針對指定的三個類別，分別提供專業分析。

    專題資料：
    {topic_data}
    """

    # 8️⃣ 呼叫 Gemini 模型
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

    return dict(pro_analyze.parsed)

def highest_category(topic_id: str):
    stories_id = supabase.table("topic_news_map").select("topic_id,story_id").eq("topic_id", topic_id).execute() # 專題中的文章
    story_ids = [item["story_id"] for item in stories_id.data]
    who_talks = supabase.table("single_news").select("story_id,who_talk").in_("story_id", story_ids).execute() # 各篇專家誰發言
    category_count = {}
    for item in who_talks.data:
        if item["who_talk"]:
            for category in item["who_talk"]["who_talk"]:
                if category in category_count:
                    category_count[category] += 1
                else:
                    category_count[category] = 1
    sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)
    top_categories = [item[0] for item in sorted_categories[:3]]
    return top_categories


all_require = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("topic").select("topic_id,who_talk").range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    all_require.extend(temp.data)
    start += batch_size

require = type("Result", (), {"data": all_require})  # 模擬原本 require 結構

all_data = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("pro_analyze_topic").select("topic_id").range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    all_data.extend([row["topic_id"] for row in temp.data])
    start += batch_size

# # 去重
constraints = list(set(all_data))

# for item in require.data:
#     if item["story_id"] in constraints:
#         continue
#     if item["who_talk"]:
#         story_id = item["story_id"]
#         who_talk = item["who_talk"]
#         results = Pro_Analyze(story_id, who_talk["who_talk"])
#         print(story_id)
#         #{'analyze': [AnalyzeItem(Category='Taiwan News', Role='結構工程技師', Analyze='該事故可能促使台灣重新檢視橋樑工程的安全標準與監管機制，避免類似事件發生，並提升公共工程品質。'), AnalyzeItem(Category='International News', Role='國際勞工安全專家', Analyze='事件突顯中國在基礎建設快速擴張下，可能存在勞工安全保障不足的問題，國際社會或將更關注中國工安標準。'), AnalyzeItem(Category='Business & Finance', Role='營建產業分析師', Analyze='或將促使在中國營運的台商重新評估其投資風險與供應鏈韌性，並可能影響相關產業的保險成本。')]}
#         for result in results["analyze"]:
#             supabase.table("pro_analyze").insert({
#                 "analyze_id": str(uuid.uuid4()),
#                 "story_id": story_id,
#                 "category": result.Category,
#                 "analyze": (result.model_dump())
#             }).execute()
#         print(f"Inserted pro_analyze for story_id {story_id} and categories {who_talk['who_talk']}")
#         break


#test
# categories = highest_category("49049c9a-1450-483a-aabd-a7cc3e5397c7")
# print(categories)
# results = Pro_Analyze_Topic("49049c9a-1450-483a-aabd-a7cc3e5397c7", categories)
# print(results)
for item in require.data:
    print(item["topic_id"])
    if item["topic_id"] in constraints:
        continue
    if item["who_talk"] == None:
        topic_id = item["topic_id"]
        categories = highest_category(topic_id)
        results = Pro_Analyze_Topic(topic_id, categories)
        print(topic_id)
        #{'analyze': [AnalyzeItem(Category='Taiwan News', Role='結構工程技師', Analyze='該事故可能促使台灣重新檢視橋樑工程的安全標準與監管機制，避免類似事件發生，並提升公共工程品質。'), AnalyzeItem(Category='International News', Role='國際勞工安全專家', Analyze='事件突顯中國在基礎建設快速擴張下，可能存在勞工安全保障不足的問題，國際社會或將更關注中國工安標準。'), AnalyzeItem(Category='Business & Finance', Role='營建產業分析師', Analyze='或將促使在中國營運的台商重新評估其投資風險與供應鏈韌性，並可能影響相關產業的保險成本。')]}
        for result in results["analyze"]:
            supabase.table("pro_analyze_topic").insert({
                "analyze_id": str(uuid.uuid4()),
                "topic_id": topic_id,
                "category": result.Category,
                "analyze": (result.model_dump())
            }).execute()
        supabase.table("topic").update({
            "who_talk": {
                "who_talk": categories
            }
        }).eq("topic_id", topic_id).execute()
        print(f"Inserted pro_analyze_topic for topic_id {topic_id} and categories {categories}")



