import logging
import uuid
from pydantic import BaseModel
from google.genai import types
from env import gemini_client, supabase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic 模型定義 (符合您要求的回傳格式) ---

class CountryAnalyzeResponse(BaseModel):
    """
    定義 Gemini 必須回傳的扁平 JSON 結構。
    """
    analyze: str          # 繁體中文分析
    analyze_en_lang: str  # 英文分析
    analyze_id_lang: str  # 印尼文分析
    analyze_jp_lang: str  # 日文分析

# --- 核心功能 ---

def generate_country_analysis(story_id: str, country: str) -> dict:
    """
    根據 story_id 和 country (目前主要為 'Taiwan') 生成分析。
    """
    
    # 1. 根據 story_id 查詢新聞內容
    try:
        response = supabase.table("single_news").select("news_title, long").eq("story_id", story_id).single().execute()
        
        if not response.data:
            logger.error(f"No news found for story_id: {story_id}")
            raise Exception("Article not found")
            
        news_title = response.data.get("news_title", "無標題")
        long_content = response.data.get("long", "無內容")
        
    except Exception as e:
        logger.error(f"Error fetching news {story_id}: {e}")
        raise

    # 2. 定義 System Instruction (角色扮演與任務)
    # 目前 'country' 參數雖然傳入，但 prompt 強調 "台灣"
    system_instruction = f"""
    你是一位頂級的「台灣新聞分析師」。你的唯一任務是分析一篇新聞，並專注於「這件事對台灣（Taiwan）的具體影響」。

    # 核心準則：
    1.  **台灣視角 (Taiwan-centric):** 你的所有分析都必須從台灣的立場出發。
    2.  **具體影響:** 不要只是總結新聞。明確指出這對台灣的「政治」、「經濟」、「社會」或「產業」可能造成的「具體後果」或「連鎖反應」。
    3.  **嚴格限制內容:** 長度保持在中文字120字以內，簡明扼要，講述重點。

    # 輸出任務：
    你必須同時產生四種語言的分析：
    1.  `analyze`: 繁體中文 (Traditional Chinese) 的分析。
    2.  `analyze_en_lang`: 英文 (English) 的分析。
    3.  `analyze_id_lang`: 印尼文 (Bahasa Indonesia) 的分析。
    4.  `analyze_jp_lang`: 日文 (Japanese) 的分析。

    # 嚴格禁止：
    -   禁止總結文章內容。
    -   禁止分析對台灣以外地區的影響。
    -   你的回覆必須嚴格遵守 Pydantic JSON Schema。
    """

    # 3. 組合 User Prompt
    user_prompt = f"""
    請根據以下新聞內容，分析這則新聞對「台灣」的具體影響。

    新聞標題: {news_title}
    新聞內文:
    ---
    {long_content}
    ---

    請嚴格按照要求的 JSON 格式輸出四種語言的分析。
    """

    # 4. 呼叫 Gemini
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", # 使用 flash 以求即時互動
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CountryAnalyzeResponse, # 套用扁平的 Pydantic Schema
            ),
        )
        
        # 將 Pydantic 物件轉為字典
        analysis_data = dict(response.parsed)
        logger.info(f"Successfully generated country analysis for {story_id}")
        return analysis_data
        
    except Exception as e:
        logger.error(f"Error calling Gemini for {story_id}: {e}")
        raise

def insert_analysis_data(story_id: str, country: str, analysis_data: dict):
    """
    將分析資料插入 'country_pro_analyze' 資料表。
    會將扁平字典中的字串轉換為 JSON 物件再插入。
    """
    
    # 為了符合 DB 欄位為 json 類型的要求，我們將 string 包裝成 object
    # 範例: "分析內容..." -> {"content": "分析內容..."}
    try:
        insert_payload = {
            "story_id": story_id,
            "country": country,
            "analyze": {"content": analysis_data.get("analyze")},
            "analyze_en_lang": {"content": analysis_data.get("analyze_en_lang")},
            "analyze_id_lang": {"content": analysis_data.get("analyze_id_lang")},
            "analyze_jp_lang": {"content": analysis_data.get("analyze_jp_lang")},
        }
        
        supabase.table("country_pro_analyze").insert(insert_payload).execute()
        logger.info(f"Successfully inserted country analysis for story_id: {story_id}")
        
    except Exception as e:
        # 即使插入失敗，前端也已經收到回應，這裡只記錄錯誤
        logger.error(f"Failed to insert country analysis for {story_id}: {e}")
        # 不需 re-raise，避免前端在已收到 200 OK 後又看到 500 錯誤