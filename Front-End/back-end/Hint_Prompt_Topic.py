from pydantic import BaseModel
from functools import lru_cache
from google import genai
from env import gemini_client , supabase
from google.genai import types
import os

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]

class Hint_Prompt_Topic:

    @staticmethod
    @lru_cache(maxsize=128)
    def generate_hint_prompt(option, topic_id, chat_content):
        """
        根據主題、專家選項和聊天紀錄生成提示詞。
        此方法會被快取，以避免對相同的輸入重複進行資料庫和 API 呼叫。
        """
        # --- 資料庫查詢 ---
        # 1. 根據 topic_id 查詢對應的 story_id 列表
        topic_news_response = supabase.table("topic_news_map").select("story_id").eq("topic_id", topic_id).execute()
        story_ids = [item["story_id"] for item in topic_news_response.data]

        # 2. 如果沒有找到任何 story_id，直接返回空列表
        if not story_ids:
            return {"Hint_Prompt": []}

        # 3. 使用 story_id 列表查詢相關文章的簡介
        response_data = supabase.table("single_news").select("short").in_("story_id", story_ids).execute()

        # --- Gemini API 呼叫 ---
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"使用者當前想跟{option}領域的專家(們)聊天，請根據關聯文章和聊天紀錄，生成1至2個最合適且能幫助使用者開始聊天的提示詞。",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
                    "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字。"
                    f"使用者目前正在閱讀這些關聯文章：{response_data.data}。"
                    f"使用者的聊天紀錄：{chat_content}。"
                    "每個提示字請務必確保與文章內容相關，並且能夠引導使用者進行深入的討論。"
                    "請根據使用者的聊天紀錄來生成更進一步的提示詞。"
                ),
                response_mime_type="application/json",
                response_schema=HintPromptResponse,
            ),
        )
        return dict(response.parsed)

    def refresh_hint_prompt(self):
        """清除 generate_hint_prompt 方法的快取。"""
        Hint_Prompt_Topic.generate_hint_prompt.cache_clear()
    
    def append_to_chat_content(self, new_content):
        """將新的聊天內容追加到現有的聊天內容中。"""
        if new_content:
            self.chat_content += "\n" + new_content