from env import supabase, gemini_client
from pydantic import BaseModel
from google import genai
from typing import List
import uuid
import time
import json
from postgrest.exceptions import APIError


def execute_builder_with_retry(builder, max_retries: int = 3):
    """Execute a postgrest request builder with retry on statement timeout."""
    for attempt in range(1, max_retries + 1):
        try:
            return builder.execute()
        except APIError as e:
            msg = str(e)
            # Detect Postgres statement timeout and retry with backoff
            if 'canceling statement due to statement timeout' in msg and attempt < max_retries:
                wait = attempt * 2
                print(f"[warn] DB statement timeout, retry {attempt}/{max_retries} after {wait}s")
                time.sleep(wait)
                continue
            # Re-raise other API errors or after max retries
            raise
    

class RelativeItem(BaseModel):
    relative_id: str
    reason: str

class RelativeNews(BaseModel):
    relatives: List[RelativeItem]

data = supabase.table("single_news").select("story_id,category,short,generated_date").range(0, 200).order("generated_date", desc=True).execute()
data = data.data
all_data = []
batch_size = 1000
start = 0

while True:
    temp = supabase.table("relative_news").select("src_story_id").range(start, start + batch_size - 1).execute()
    if not temp.data:
        print(len(all_data))
        break
    all_data.extend([row["src_story_id"] for row in temp.data])
    start += batch_size

# 去重
constraints = list(set(all_data))

# m_data = json.dumps(data, indent=4)
# with open("relative_json.json", "w") as f:
#     f.write(m_data)

def filter_related_news(current_story: dict, all_stories: list[dict]) -> list[dict]:
    """
    使用 Gemini 篩選與 current_story 相關的新聞
    :param current_story: 當前新聞 story (dict, 包含 story_id,category,short,generated_date等)
    :param all_stories: 所有候選 story (list of dict)
    :return: 相關 story (list of dict)
    """

    current_short = current_story["short"]

    # 建立候選新聞的假 ID 與真實 story_id 的映射表
    id_to_story_map = {
        str(i + 1): story["story_id"] for i, story in enumerate(all_stories) if story["story_id"] != current_story["story_id"]
    }

    # 使用假 ID 生成候選新聞列表
    candidate_shorts = [
        story["short"] for story in all_stories if story["story_id"] != current_story["story_id"]
    ]
    candidate_list = "\n".join(f"{i+1}. {t}" for i, t in enumerate(candidate_shorts))

    prompt = f"""
    你是一個新聞分析助手。
    我會提供一則「當前新聞」和多則「候選新聞」。
    請判斷哪些候選新聞與當前新聞「高度相關」，並回傳各個相關新聞的編號和相關的原因(務必使用繁體中文)。
    確保回傳的編號個數與原因個數一致，要呈現1對1的狀態。
    在撰寫理由時，請不要提及「當前新聞」或「候選新聞」這些詞彙，而是直接描述，因為這是給使用者看的，希望能夠讓使用者理解為什麼這些新聞是相關的。
    最多回傳 3 個相關新聞，且不能有重複新聞，如果違反將會受到嚴厲懲罰。

    當前新聞：
    {current_short}

    候選新聞：
    {candidate_list}
    """

    # 嘗試呼叫 Gemini API 並取得 parsed.relatives；若失敗則重試幾次
    max_retries = 3
    relatives = None
    for attempt in range(1, max_retries + 1):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RelativeNews,
                ),
            )
            parsed = getattr(response, "parsed", None)
            if parsed and getattr(parsed, "relatives", None):
                relatives = parsed.relatives
                break
            else:
                print(f"[warn] Gemini returned no parsed data (attempt {attempt}/{max_retries}).")
        except Exception as e:
            print(f"[error] Gemini generate_content failed (attempt {attempt}/{max_retries}): {e}")

        if attempt < max_retries:
            time.sleep(attempt)  # backoff

    if not relatives:
        print(f"[error] Failed to get parsed relatives for story {current_story.get('story_id')}. Skipping.")
        return []
    related_story_ids = []
    for item in relatives:
        fake_id = item.relative_id
        if fake_id in id_to_story_map:
            real_id = id_to_story_map[fake_id]
            related_story_ids.append(real_id)

    # 篩選相關新聞
    related_stories = [
        story for story in all_stories if story["story_id"] in related_story_ids
    ]

    results = [
    {
        "story_id": story["story_id"],
        "reason": next(item.reason for item in relatives if id_to_story_map[item.relative_id] == story["story_id"])
    }
    for story in related_stories
    ]

    return results

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
    # 將當前新聞與其他新聞進行相關性篩選
    other_stories = data[:i] + data[i+1:]  # 排除當前新聞
    #確保 other_stories 中的category與current_story相同
    other_stories = [story for story in other_stories if story["category"] == current_story["category"]]
    related_news = filter_related_news(current_story, other_stories)

    if not related_news:
        print(f"No related news found or failed for {current_story['story_id']}. Continue.")
        continue

    for j, rel in enumerate(related_news):
        related_story_id = rel["story_id"]
        reason = rel["reason"]

        # 僅在 Supabase 中不存在相同 src/dst 組合時才插入
        try:
            exists_builder = (
                supabase.table("relative_news")
                .select("id")
                .eq("src_story_id", current_story["story_id"])
                .eq("dst_story_id", related_story_id)
                .limit(1)
            )
            exists_check = execute_builder_with_retry(exists_builder)
        except Exception as e:
            print(f"[error] DB exists_check failed for src:{current_story['story_id']} dst:{related_story_id}: {e}")
            # 跳過此相關項以避免中斷整個流程
            continue

        if not getattr(exists_check, 'data', None):  # 無重複，執行插入
            try:
                insert_builder = (
                    supabase.table("relative_news")
                    .insert({
                        "id": str(uuid.uuid4()),  # 生成唯一 ID
                        "reason": reason,  # 插入相關原因
                        "src_story_id": current_story["story_id"],  # 當前新聞的 story_id
                        "dst_story_id": related_story_id  # 相關新聞的 story_id
                    })
                )
                response = execute_builder_with_retry(insert_builder)
            except Exception as e:
                print(f"[error] DB insert failed for src:{current_story['story_id']} dst:{related_story_id}: {e}")
                continue

        # 最多插入三筆相關新聞（以處理到的順序為準）
        print(j)
        if j >= 2:
            break

    print(i)
    time.sleep(5)