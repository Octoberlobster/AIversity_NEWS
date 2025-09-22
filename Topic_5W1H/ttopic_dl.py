from supabase import create_client, Client
import os

# 連線到 Supabase
url = os.getenv("SUPABASE_URL")  # 換成你的 Supabase URL
key = os.getenv("SUPABASE_KEY")  # 換成你的 Key
supabase: Client = create_client(url, key)

# 查詢 topic_id 對應的所有 story_id
topic_id = "49cbf695-7d16-4558-aaa3-79b8a17997f5"

response = supabase.table("topic_news_map") \
    .select("story_id") \
    .eq("topic_id", topic_id) \
    .execute()

# 把結果存成 list
story_ids = [row["story_id"] for row in response.data]

print(story_ids)
