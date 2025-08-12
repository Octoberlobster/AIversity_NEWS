from pydantic import BaseModel
from google.genai import types
from env import gemini_client
import Knowledge_Base

model_flag = ["Science & Technology"] # 改前端的選擇結果

#TODO : 修改model_dict只有9個領域，增加專題的model與首頁搜尋的model

#這邊讀檔要改成database抓
Knowledge_Base.set_knowledge_base("./demo/news-platform/chatroom/cleaned_final_new.json")
model_dict = {
    "Politics": -1,
    "Taiwan News": -1,
    "Science & Technology": -1,
    "International News": -1,
    "Lifestyle & Consumer News": -1,
    "Sports": -1,
    "Entertainment": -1,
    "Business & Finance": -1,
    "Health & Wellness": -1,
}


class ChatInfo(BaseModel):
    name: str
    chat_response: str
    related_news: list[str]

def create_model(category):
    # 要設定json格式的話再參考https://ai.google.dev/gemini-api/docs/migrate?hl=zh-tw

    # 這部份確定再加
    # like_RAG_data = (
    #     supabase.table("generated_news")
    #     .select("content")
    #     .eq("category", category)
    #     .execute()
    # )

    model = "gemini-2.0-flash"
    if category in model_dict:
        if model_dict[category] != -1:
            return model_dict[category]
        else:
            model_dict[category] = gemini_client.chats.create(
                model=model,
                config=types.GenerateContentConfig(
                    system_instruction=Knowledge_Base.get_knowledge_base(category),
                    response_mime_type="application/json",
                    response_schema=ChatInfo,
                ),
            )
            return model_dict[category]
    else:
        raise ValueError("Unknown category: {}".format(category))

def chat(prompt, categories):
    responses = []
    for category in categories:
        model = create_model(category)
        
        response = model.send_message(message=prompt)
        responses.append(dict(response.parsed))  # 將回應加入列表
    return responses

# prompt = "你知道甚麼新聞"
# category_response = chat(prompt, model_flag)
# print(category_response)
# print(type(category_response))
# print("------")