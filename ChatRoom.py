from google import genai
from google.genai import types
from pydantic import BaseModel
from supabase import create_client, Client
from flask import jsonify
import os

# 設定環境變數
api_key = os.getenv("API_KEY_Gemini")
gemini_client = genai.Client(api_key=api_key)
api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("Supabase_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

model_flag = ["Politics","Science","Technology"] # 改前端的選擇結果

model_dict = {
    "Politics": -1,
    "Social News": -1,
    "Science": -1,
    "Technology": -1,
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

    if category == "Politics":
        system_instruction = "你是政治專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Social News":
        system_instruction = "你是社會新聞專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Science":
        system_instruction = "你是科學專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Technology":
        system_instruction = "你是科技專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "International News":
        system_instruction = "你是國際新聞專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Lifestyle & Consumer News":
        system_instruction = "你是生活與消費新聞專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Sports":
        system_instruction = "你是體育專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Entertainment":
        system_instruction = "你是娛樂專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Business & Finance":
        system_instruction = "你是商業與金融專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    elif category == "Health & Wellness":
        system_instruction = "你是健康與福祉專家"
        return gemini_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
    else:
        raise ValueError("Unknown category: {}".format(category))

def chat(prompt, categories):
    responses = []
    for category in categories:
        if model_dict[category] == -1:
            model_dict[category] = create_model(category)
        
        response = model_dict[category].send_message(message=prompt)
        responses.append(dict(response.parsed))  # 將回應加入列表
    return responses

# prompt = "你好"
# category_response = chat(prompt, model_flag)
# print(category_response)

    

