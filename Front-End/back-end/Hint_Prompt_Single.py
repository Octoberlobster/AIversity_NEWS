from pydantic import BaseModel
from functools import lru_cache
from google.genai import types
from env import gemini_client
import os

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]

# <<< ADDED LANGUAGE MAPPING >>>
language_map = {
    "zh-TW": "繁體中文 (Traditional Chinese)",
    "en-US": "English (US)",
    "ja-JP": "日本語 (Japanese)",
    "id-ID": "Bahasa Indonesia (Indonesian)"
}

# @lru_cache(maxsize=128)
# def generate_hint_prompt(option,article,chat_content):
#     ... (omitted old code) ...

class Hint_Prompt_Single:
    def __init__(self,chat_content):
        self.chat_content = chat_content

    @staticmethod
    @lru_cache(128)
    def generate_hint_prompt(option, article, chat_content, language="zh-TW"): # <<< MODIFIED
        
        # <<< ADDED LANGUAGE INSTRUCTION >>>
        output_language = language_map.get(language, "繁體中文 (Traditional Chinese)")
        language_instruction = f"\n\n# 語言規則\n- 你必須嚴格使用「{output_language}」來回覆所有提示詞。"
        
        # <<< MODIFIED system_instruction >>>
        original_instruction = (
            "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
            "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字"
            f"使用者正在閱讀的文章是：{article}，"
            f"使用者的聊天紀錄：{chat_content}，"
            "每個提示字請務必確保與文章內容相關，並且能夠引導使用者進行深入的討論。"
            "除此之外，你會接收到使用者的聊天紀錄，請根據使用者的聊天紀錄來生成更進一步的提示詞。"
        )

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents= f"使用者當前想跟{option}領域的專家(們)聊天，生成1至2個最合適且能幫助使用者開始聊天的提示詞。",
            config=types.GenerateContentConfig(
                system_instruction=original_instruction + language_instruction, # <<< MODIFIED
                response_mime_type="application/json",
                response_schema=HintPromptResponse,
            ),
        )
        return dict(response.parsed)
    
    def refresh_hint_prompt(self):
        self.generate_hint_prompt.cache_clear()

    def append_to_chat_content(self, new_content):
        self.chat_content += new_content

# ... (omitted test code) ...