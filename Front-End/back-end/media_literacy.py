import logging
import uuid
from pydantic import BaseModel
from google.genai import types
from env import gemini_client, supabase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic 模型定義 (符合您要求的回傳格式) ---

class MediaLiteracyResponse(BaseModel):
    """
    定義 Gemini 必須回傳的扁平 JSON 結構，對應 media_literacy 資料表欄位。
    """
    alert: str          # 繁體中文提醒
    alert_en_lang: str  # 英文提醒
    alert_id_lang: str  # 印尼文提醒
    alert_jp_lang: str  # 日文提醒

# --- 核心功能 ---

def generate_media_literacy_alert(story_id: str) -> dict:
    """
    根據 story_id 生成媒體識讀提醒。
    會抓取新聞標題、內容以及 suicide_flag 來判斷提醒的嚴肅程度。
    """
    
    # 1. 根據 story_id 查詢新聞內容
    try:
        response = supabase.table("single_news").select("news_title, long, suicide_flag").eq("story_id", story_id).single().execute()
        
        if not response.data:
            logger.error(f"No news found for story_id: {story_id} (media_literacy)")
            raise Exception("Article not found")
            
        news_title = response.data.get("news_title", "無標題")
        long_content = response.data.get("long", "無內容")
        # 處理 suicide_flag 可能為 None 的情況
        suicide_flag = response.data.get("suicide_flag", False) 
        
    except Exception as e:
        logger.error(f"Error fetching news {story_id} (media_literacy): {e}")
        raise

    # 2. 根據 suicide_flag 動態決定 Prompt 的強調指令
    if suicide_flag:
        special_emphasis_instruction = (
            "！！！重大警告：此新聞包含自殺或抑鬱相關內容 (suicide_flag=True)。\n"
            "你的提醒「必須」用更嚴肅和關懷的語氣。重點：\n"
            "1. 強烈建議讀者謹慎對待 AI 在此敏感議題上的描述。\n"
            "2. 提醒 AI 可能無法理解此事的嚴重性或細微差別。\n"
            "3. 鼓勵尋求專業協助，而不是僅依賴 AI 資訊。\n"
            "這是最高優先級！"
        )
        # 稍微提高溫度以增加關懷感
        generation_temperature = 0.6
    else:
        special_emphasis_instruction = (
            "一般準則：此新聞 (suicide_flag=False) 為一般內容。\n"
            "請專注於 AI 內容核實的基本提醒，鼓勵多方查證。"
        )
        # 媒體識讀提醒應保持一致性
        generation_temperature = 0.4

    # 3. 定義 System Instruction (角色扮演與任務)
    system_instruction = f"""
    你是一位頂級的「媒體識讀專家」與「AI 內容分析師」。

    # 核心任務
    你的唯一任務是分析一篇「由 AI 產生的新聞」，並提供一段簡短（約 50-80 字）的「媒體識讀提醒」。
    這段提醒的目的是告訴讀者，在閱讀這篇 AI 新聞時應該注意什麼。

    # 核心準則
    1.  **強調 AI 來源：** 必須溫和地提醒讀者，這篇文章是由 AI 生成的，內容可能包含錯誤、偏見或過時資訊，需要獨立核實。
    2.  **批判性思維：** 鼓勵讀者保持批判性思維，並從多方來源查證資訊。
    3.  **避免恐慌：** 你的語氣應該是「提醒」而非「警告」（除非 suicide_flag 為 True）。
    4.  **簡潔扼要：** 提醒內容必須精煉，直接切入重點。

    # {special_emphasis_instruction}

    # 輸出任務
    你必須同時產生四種語言的提醒（內容必須簡潔、切中要點）：
    1.  `alert`: 繁體中文 (Traditional Chinese)
    2.  `alert_en_lang`: 英文 (English)
    3.  `alert_id_lang`: 印尼文 (Bahasa Indonesia)
    4.  `alert_jp_lang`: 日文 (Japanese)

    # 嚴格禁止
    -   禁止總結文章內容。
    -   你的回覆必須嚴格遵守 Pydantic JSON Schema。
    """

    # 4. 組合 User Prompt
    # 截斷部分內容，避免 Prompt 過長
    user_prompt = f"""
    請根據以下 AI 生成的新聞內容，分析並產生四種語言的「媒體識讀提醒」。

    新聞標題: {news_title}
    新聞內文 (部分):
    ---
    {long_content[:1500]}... 
    ---
    (分析依據: suicide_flag = {suicide_flag})

    請嚴格按照要求的 JSON 格式輸出四種語言的提醒。
    """

    # 5. 呼叫 Gemini
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", # 使用 flash 以求即時互動
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=MediaLiteracyResponse, # 套用 Pydantic Schema
                temperature=generation_temperature # 根據 suicide_flag 動態調整
            ),
        )
        
        # 將 Pydantic 物件轉為字典
        alert_data = dict(response.parsed)
        logger.info(f"Successfully generated media literacy alert for {story_id}")
        return alert_data
        
    except Exception as e:
        logger.error(f"Error calling Gemini for {story_id} (media literacy): {e}")
        raise

def insert_media_literacy_data(story_id: str, alert_data: dict):
    """
    將媒體識讀提醒資料插入 'media_literacy' 資料表。
    此處的欄位是 text，不需要像 country_pro_analyze 一樣包裝成 {"content": ...}
    """
    
    try:
        insert_payload = {
            "story_id": story_id,
            "alert": alert_data.get("alert"),
            "alert_en_lang": alert_data.get("alert_en_lang"),
            "alert_id_lang": alert_data.get("alert_id_lang"),
            "alert_jp_lang": alert_data.get("alert_jp_lang"),
            # media_literacy_id 會由資料庫 default gen_random_uuid() 自動生成
        }
        
        supabase.table("media_literacy").insert(insert_payload).execute()
        logger.info(f"Successfully inserted media literacy alert for story_id: {story_id}")
        
    except Exception as e:
        # 即使插入失敗，前端也已經收到回應，這裡只記錄錯誤
        logger.error(f"Failed to insert media literacy alert for {story_id}: {e}")
        # 不需 re-raise，避免前端在已收到 200 OK 後又看到 500 錯誤