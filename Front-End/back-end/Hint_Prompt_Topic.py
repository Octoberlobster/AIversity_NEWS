from pydantic import BaseModel
from google import genai
from env import gemini_client , supabase
from google.genai import types
import os

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]

class Hint_Prompt_Topic:
    def __init__(self):
        self.model_instance = None
        self.topic_id = None

    def _create_model(self):
        model_name = "gemini-2.0-flash"
        # 先執行內部查詢，獲取 story_id 列表
        topic_news_response = supabase.table("topic_news_map").select("story_id").eq("topic_id", self.topic_id).execute()
        story_ids = [item["story_id"] for item in topic_news_response.data]  # 提取 story_id 列表

        # 使用提取的 story_id 列表進行查詢
        response = supabase.table("single_news").select("short").in_("story_id", story_ids).execute()

        return gemini_client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
                    "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字，生成1至2個提示詞。"
                    f"使用者目前正在閱讀這些文章：{response.data}。"
                    "每個提示字請務必確保與文章內容相關，並且能夠引導使用者進行深入的討論。"
                    "除此之外，你會接收到使用者的聊天紀錄，請根據使用者的聊天紀錄來生成更進一步的提示詞。"
                ),
                response_mime_type="application/json",
                response_schema=HintPromptResponse,
            ),
        )

    def get_model(self):
        if self.model_instance is None:
            self.model_instance = self._create_model()
        return self.model_instance

    def generate_hint_prompt(self, prompt = None):
        model = self.get_model()
        response = model.send_message(message=prompt)
        
        return dict(response.parsed)