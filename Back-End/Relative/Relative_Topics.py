from env import supabase, gemini_client
from pydantic import BaseModel
from google import genai
from typing import List
import uuid
import time
    

class RelativeItem(BaseModel):
    relative_id: str
    reason: str

class RelativeTopics(BaseModel):
    relatives: List[RelativeItem]

response = supabase.table("single_news").select("story_id,category,short,generated_date").execute()
topics = supabase.table("topic").select("topic_id,topic_title,topic_short").execute()

all_data = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("relative_topics").select("src_story_id").range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    all_data.extend([row["src_story_id"] for row in temp.data])
    start += batch_size

# 去重
constraints = list(set(all_data))
topics = topics.data
data = response.data

# m_data = json.dumps(data, indent=4)
# with open("relative_json.json", "w") as f:
#     f.write(m_data)

# 假設 topic_news_map 是一個字典，包含專題與相關新聞的對應關係
topic_news_map = supabase.table("topic_news_map").select("*").execute().data

def filter_related_topics(current_story: dict, all_topics: list[dict]) -> list[dict]:
    """
    確認 current_story 是否已在 topic_news_map 中，若在則直接視為相關專題之一。
    否則，使用 Gemini 進行分類，最多返回兩個相關專題，並確保理由可信。
    """
    current_short = current_story["short"]
    related_topics = []


    # 建立候選新聞的假 ID 與真實 topic_id 的映射表
    id_to_story_map = {f"{i+1}": topic["topic_id"] for i, topic in enumerate(all_topics)}
    

    # 使用假 ID 生成候選專題列表
    candidate_list = "\n".join(f"{i+1}. {topic['topic_short']}" for i, topic in enumerate(all_topics))


    prompt = f"""
你是一個專業的新聞分析助手，擅長從內容中找出真正有意義的主題關聯。

我會提供一則「當前新聞」和多則「候選專題」。
請嚴格判斷哪些候選專題與新聞內容有「高度直接相關性」。
所謂「高度直接相關性」指的是：
- 兩者在主題、事件、人物、政策、產業或影響層面上有明確、具體的交集；
- 而不是僅僅因為屬於相似領域或抽象概念而牽強連結。

你的任務：
1. 選出最多 2 個與新聞內容高度相關的專題。
2. 回傳每個相關專題的編號與理由。
3. 每一個理由都要清楚說明兩者之間具體的連結點，例如共同事件、影響機制、相同政策背景、或同一產業脈絡。
4. 確保回傳的「編號數量」與「理由數量」一致，呈現一對一的對應關係。
5. 在理由中不要使用「當前新聞」或「候選專題」等字眼，要以自然的方式呈現關聯原因，讓讀者能直接理解兩者的具體關聯性。

當前新聞：
{current_short}

候選專題：
{candidate_list}
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RelativeTopics,
        ),
    )

    # 將假 ID 轉換為真實的 topic_id
    relatives = response.parsed.relatives
    for item in relatives:
        fake_id = item.relative_id
        if fake_id in id_to_story_map:
            real_id = id_to_story_map[fake_id]
            related_topics.append({
                "topic_id": real_id,
                "reason": item.reason
            })

    # 返回最多兩個相關專題
    return related_topics

# print(data[0])
# one = filter_related_news(data[0], data[1:])
# print(one)
# #insert database
# response = (
#     supabase.table("relative_news")
#     .insert({"id": str(uuid.uuid4()),"reason":one[0]["reason"], "src_story_id": data[0]["story_id"], "dst_story_id": one[0]["story_id"]})
#     .execute()
# )

for i, current_story in enumerate(data):
    #constraints is a list like [0,1,2,3,4,5]
    if current_story["story_id"] in constraints:
        print(f"Skipping {current_story['story_id']} as it already exists in constraints.")
        continue
    # 檢查 current_story 是否已在 topic_news_map 中
    if any(mapping["story_id"] == current_story["story_id"] for mapping in topic_news_map):
        topic_id = next(mapping["topic_id"] for mapping in topic_news_map if mapping["story_id"] == current_story["story_id"])
    #topics中將topic_id除外
        other_topics = [topic for topic in topics if topic["topic_id"] != topic_id]
    else:
        other_topics = topics
        topic_id = None
    related_topics = filter_related_topics(current_story, other_topics)
    #related_topics append topic_id
    if topic_id:
        related_topics.append({"topic_id": topic_id, "reason": "這篇新聞在這篇專題中。"})

    for j in range(len(related_topics)):
        related_topic_id = related_topics[j]["topic_id"]
        reason = related_topics[j]["reason"]
        response = (
            supabase.table("relative_topics")
            .insert({
                "id": str(uuid.uuid4()),  # 生成唯一 ID
                "reason": reason,  # 插入相關原因
                "src_story_id": current_story["story_id"],  # 當前新聞的 story_id
                "dst_topic_id": related_topic_id  # 相關新聞的 story_id
            })
            .execute()
        )
    print(i)
    time.sleep(15)