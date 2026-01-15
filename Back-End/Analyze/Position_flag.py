from google.genai import types
from pydantic import BaseModel
from env import gemini_client, supabase

class Position_flag(BaseModel):
    flag: bool

def set_position_flag(story_id: str):
    response = supabase.table("single_news").select("story_id,long").eq("story_id", story_id).execute()
    model_name = "gemini-2.5-flash-lite"
    position_flag = gemini_client.models.generate_content(
        model=model_name,
        contents=response.data[0]["long"],
        config=types.GenerateContentConfig(
            system_instruction="請根據文章內容，判斷該新聞是否有正反兩方討論的空間，是篇能夠產生兩極對立衝突的新聞，若有請回傳True，若沒有請回傳False。",
            response_mime_type="application/json",
            response_schema=Position_flag,
        ),
    )   
    return dict(position_flag.parsed)

def fetch_all_data(categories):
    all_require = []
    batch_size = 1000
    start = 0

    while True:
        temp = supabase.table("single_news").select("story_id,category,position_flag").in_("category", categories).range(start, start + batch_size - 1).execute()
        if not temp.data:
            break
        all_require.extend(temp.data)
        start += batch_size

    return type("Result", (), {"data": all_require})  # 模擬原本 require 結構

categories2 = ["Science & Technology", "Lifestyle & Consumer", "Sports", "Entertainment", "Business & Finance", "Health & Wellness", "Germany", "France", "Spain", "UK", "United States of America", "Vietnam", "Japan", "Korea", "India", "Australia", "Indonesia", "Philippines"]
require = fetch_all_data(categories2)
for item in require.data:
    if item["position_flag"] is None:
        story_id = item["story_id"]
        supabase.table("single_news").update({"position_flag": "FALSE"}).eq("story_id", story_id).execute()
        print(f"Updated story_id {story_id} with position_flag FALSE")
    else:
        print(f"story_id {item['story_id']} already has position_flag {item['position_flag']}")
    # break

categories = ["Politics", "International News"]
require = fetch_all_data(categories)
for item in require.data:
    if item["position_flag"] is None:
        story_id = item["story_id"]
        result = set_position_flag(story_id)
        supabase.table("single_news").update({"position_flag": result["flag"]}).eq("story_id", story_id).execute()
        print(f"Updated story_id {story_id} with position_flag {result['flag']}")
    else:
        print(f"story_id {item['story_id']} already has position_flag {item['position_flag']}")
    # break
print("All done.")