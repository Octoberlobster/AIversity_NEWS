from supabase import create_client, Client
import json
import os
from collections import defaultdict

api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("Supabase_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

response = (
    supabase.from_("event_original_map")
    .select("event_id,cleaned_news(title, content)")
    .execute()
)
data = response.data


# 假設你的資料叫 data_list
grouped = defaultdict(list)

for item in data:
    event_id = item["event_id"]
    grouped[event_id].append(item["cleaned_news"])

# 如果你需要轉成普通 dict（不是 defaultdict）
grouped_dict = dict(grouped)

print(grouped_dict)









