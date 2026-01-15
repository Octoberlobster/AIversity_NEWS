from pydantic import BaseModel
from google import genai
from google.genai import types
from env import gemini_client, supabase
import os
import logging

# <<< 新增
logger = logging.getLogger(__name__)

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]

# <<< ADDED LANGUAGE MAPPING >>>
language_map = {
    "zh-TW": "繁體中文 (Traditional Chinese)",
    "en-US": "English (US)",
    "ja-JP": "日本語 (Japanese)",
    "id-ID": "Bahasa Indonesia (Indonesian)"
}

def generate_hint_prompt(language="zh-TW"): # <<< MODIFIED
    
    # <<< ADDED LANGUAGE INSTRUCTION >>>
    output_language = language_map.get(language, "繁體中文 (Traditional Chinese)")
    language_instruction = f"\n\n# 語言規則\n- 你必須嚴格使用「{output_language}」來回覆所有提示詞。"

    # --- MODIFICATION START ---
    try:
        # 透過 !inner JOIN 一次性查詢 single_news 並過濾 stories.country
        response = (
            supabase.table("single_news")
            .select("news_title, long, stories!inner(country)") # 請求 JOIN
            .eq("stories.country", "Taiwan")  # 對 JOIN 的 'stories' 表下篩選條件
            .order("generated_date", desc=True)
            .limit(10) # 限制 10 筆
            .execute()
        )
        news = response.data
    
    except Exception as e:
         logger.error(f"Error fetching news for hint_prompt_search: {e}")
         news = [] # 發生錯誤時，回退到空列表
    # --- MODIFICATION END ---
    
    # <<< MODIFIED system_instruction >>>
    original_instruction = (
        "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
        "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字"
        "每個提示字請務必確保能讓使用者展開對於時事新聞的討論。"
        "並且確保只產生3個提示詞"
    )
    
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents= f"請根據最新的熱門時事新聞{news}，生成 3 個最合適且能幫助使用者開始聊天的提示詞。",
        config=genai.types.GenerateContentConfig(
            system_instruction=original_instruction + language_instruction, # <<< MODIFIED
            response_mime_type="application/json",
            response_schema=HintPromptResponse,
        ),
    )
    return dict(response.parsed)


# #test in terminal
# response = generate_hint_prompt()
# print(response)