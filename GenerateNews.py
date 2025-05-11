import google.generativeai as genai
import json
from time import sleep
import os
from supabase import create_client, Client
from collections import defaultdict
import uuid

api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("Supabase_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

model = genai.GenerativeModel('gemini-1.5-pro-002')

response = (
    supabase.from_("event_original_map")
    .select("event_id,cleaned_news(title,url,content,date)")
    .execute()
)
data = response.data
# 將資料轉換為字典格式
grouped = defaultdict(list)

for item in data:
    event_id = item["event_id"]
    grouped[event_id].append(item["cleaned_news"])

grouped_dict = dict(grouped)

for event_id, data in grouped_dict.items():
    News_body = json.dumps(data, ensure_ascii=False, indent=4)
    News=model.generate_content("請根據以下彙整的新聞內容，生成一篇新的新聞報導，並提供標題與統整內容。請確保內容具有新聞性，並清楚呈現事件的背景、發展與影響。"
                                "輸出格式（請以 JSON 格式回傳）："
                                "{"
                                "\"title\": \"請生成一個符合新聞風格的標題\","
                                "\"content\": \"請綜合以下新聞內容，撰寫一篇具邏輯性、流暢且完整的新聞報導\","
                                "\"date\": \"請填寫新聞生成的日期（格式：YYYY-MM-DD）\","
                                f"\"event_id\": \"{event_id}\""
                                "}"
                                f"需要彙整的新聞內容：\n{News_body}"
                                "請確保新生成的新聞報導符合以下要求："
                                "維持新聞的公正與專業性"
                                "使用清晰且具邏輯性的語句"
                                "確保內容與事實相符，不加入虛構或未經證實的資訊"
                                )
    News = News.text
    News = News.replace('```json', '').replace('```', '').strip()
    News = json.loads(News)
    
    m_uuid = uuid.uuid4()
    response = (
        supabase.table("generated_news")
        .insert({"generated_id": str(m_uuid),
                 "title": News["title"],
                 "content": News["content"],
                 "date": News["date"],
                 "event_id": News["event_id"]})
        .execute()
    )
    sleep(1)
    
   






