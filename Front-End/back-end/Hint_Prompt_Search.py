from pydantic import BaseModel
from google import genai
from google.genai import types
from env import gemini_client, supabase
import os

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]


def generate_hint_prompt():
    response = supabase.table("single_news").select("news_title,long").order("generated_date", desc=True).limit(10).execute()
    news = response.data
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents= f"請根據最新的熱門時事新聞{news}，生成 3 個最合適且能幫助使用者開始聊天的提示詞。",
        config=genai.types.GenerateContentConfig(
            system_instruction=(
                "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
                "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字"
                "每個提示字請務必確保能讓使用者展開對於時事新聞的討論。"
                "並且確保只產生3個提示詞"
            ),
            response_mime_type="application/json",
            response_schema=HintPromptResponse,
        ),
    )
    return dict(response.parsed)


# #test in terminal
# response = generate_hint_prompt()
# print(response)