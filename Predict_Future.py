import google.generativeai as genai
from supabase import create_client, Client
import json
import os
from collections import defaultdict

api_key = os.getenv("API_KEY_Ge")
genai.configure(api_key=api_key)

SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

model = genai.GenerativeModel('gemini-1.5-pro-002')

chat_session = model.start_chat(history=[])
first_message = "接下來我會給你一連串的新聞內容，這些內容都已經依照發生順序給分類好了，請你記得這些內容，在最後提到\"預測未來\"時請你幫我根據先前的內容以三種面向來預測近日可能發生的未來(用十五到二十個字之間對每個面向總結除此之外生成關於這篇預測的標題即可)，" \
                "請你以在預測時以JSON格式回答格式如下:"\
                "{"\
                "\"title\": \"請生成一個符合預測的標題\","\
                "\"content\": [\"1.\"\"2.\"\"3.\"],"\
                "}"\
                "如果你有接收到我的指示，請一律回答\"是的\"，謝謝！"
chat_session.send_message(first_message)

response = (
    supabase.table("generated_news")
    .select("generated_id, event_id")
    .execute()
)
response = response.data
for i in range(len(response)):
    original_news =(
        supabase.table("event_original_map")
        .select("event_id,cleaned_news(content,date)")
        .eq("event_id", response[i]["event_id"])
        .order("cleaned_news(date)", desc=False)
        .execute()
    )
    original_news = original_news.data
    print(original_news)
    grouped = defaultdict(list)

    for item in original_news:
        event_id = item["event_id"]
        grouped[event_id].append(item["cleaned_news"]["content"])

    grouped_dict = dict(grouped)
    for event_id, data in grouped_dict.items():
        News_body = json.dumps(data, ensure_ascii=False, indent=4)
        chat_session.send_message(News_body)
    Predict=chat_session.send_message("預測未來")
    Predict = Predict.text
    Predict = Predict.replace('```json', '').replace('```', '').strip()
    Predict = json.loads(Predict)
    total_content = ""
    for j in range(len(Predict["content"])):
        total_content += Predict["content"][j]
        total_content += "\n"
    Predict["content"] = total_content
    update_response = (
        supabase.table("generated_news")
        .update({"predict_title": Predict["title"],
                 "predict_content": Predict["content"]})
        .eq("generated_id", response[i]["generated_id"])
        .execute()
    )
        
   