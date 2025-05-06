import google.generativeai as genai
from supabase import create_client, Client
import json
from time import sleep
import os
import uuid

api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)

api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

model = genai.GenerativeModel('gemini-1.5-pro-002')

response = (
    supabase.table("cleaned_news")
    .select("sourcecle_id,title, url, content, date")
    .gte("date","2025-05-05T22:19:59")
    .execute()
)
data = response.data
summaries = []

for i in range(len(data)):
    data_str = json.dumps(data[i], ensure_ascii=False, indent=4)
    summary = model.generate_content("請根據下列新聞文本生成一份摘要，"
                                     "並萃取出主要的關鍵字，"
                                     "請注意要提取出事件的核心描述、關鍵人物、地點或機構。"
                                     "請以 JSON 格式回傳，格式如下："
                                     "{"
                                     "\"summary\": \"摘要內容\","
                                     "\"key\": [\"關鍵字1\", \"關鍵字2\", ...],"
                                     "\"date\": \"YYYY-MM-DD\""
                                     "\"url\": \"新聞網址\""
                                     "\"index\": \"sourcecle_id\""
                                     "}"
                                     "新聞文本："+data_str
                                     )      
    summary = summary.text
    summary = summary.replace('```json', '').replace('```', '').strip()
    summary = json.loads(summary)
    summaries.append(summary)
    print(i)
    sleep(0.5)
# with open ("Summaries.json", "w", encoding="utf-8") as file:
#     json.dump(summaries, file, ensure_ascii=False, indent=4)
summaries_str = json.dumps(summaries, ensure_ascii=False, indent=4)

Categorize = model.generate_content("請根據下列多則新聞摘要，將它們分群以識別屬於同一事件的新聞。分群時，請考慮以下依據："
                               "1. 事件描述的相似度（摘要內容）"
                               "2. 關鍵字的重合率"
                               "3. 事件日期是否接近"
                               "4. 重要關鍵人物或地點是否一致"
                               "5. 每篇新聞都要有他們所屬的事件"
                               "6. 請勿混淆不同事件的新聞，並且只以存在的資料來進行分類事件"
                               "請以 JSON 格式回傳分群結果，格式範例如下："
                               "{"
                               "\"事件名稱1(請你幫忙取名)\":{"
                               "\"index\": [個別的index],"
                               "\"key\": [\"關鍵字1\", \"關鍵字2\", \"關鍵字3\"],"
                               "\"date\": \"YYYY-MM-DD\""
                               "},"
                               "\"事件名稱2(請你幫忙取名)\":{"
                               "\"index\": [個別的index],"
                               "\"key\": [\"關鍵字4\", \"關鍵字5\", \"關鍵字6\"],"
                               "\"date\": \"YYYY-MM-DD\""    
                               "},"
                               "..."
                               "}"
                               + 
                               "以下是需要請你分類的新聞摘要："
                               +summaries_str)
Categorize = Categorize.text
Categorize = Categorize.replace('```json', '').replace('```', '').strip()
Categorize = json.loads(Categorize)
# with open ("Categorize.json", "w", encoding="utf-8") as file:
#     json.dump(Categorize, file, ensure_ascii=False, indent=4)
for event_title,info in Categorize.items():
    m_uuid = uuid.uuid4()
    source_index = info["index"]
    keys = info["key"]
    response = (
        supabase.table("event")
        .insert({"event_id":str(m_uuid),"event_title":event_title})
        .execute()
    )
    for source in source_index:
        response = (
            supabase.table("event_original_map")
            .insert({"event_id":str(m_uuid),"sourcecle_id":source})
            .execute()
        )
    for key in keys:
        response = (
            supabase.table("event_keyword_map")
            .insert({"event_id":str(m_uuid),"keyword":key})
            .execute()
        )


