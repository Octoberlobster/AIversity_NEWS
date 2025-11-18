# back-end/media_literacy.py

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

# --- Kärnfunktioner ---

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
        generation_temperature = 0.7 
    else:
        special_emphasis_instruction = (
            "一般準則：此新聞 (suicide_flag=False) 為一般內容。\n"
            "你的提醒必須將「AI 提醒」與「情境建議」自然地融合在一起。"
        )
        generation_temperature = 0.9 

    # 3. 定義 System Instruction (角色扮演與任務)
    # <<< MODIFIED v3: 這是修改後的新版本，導入「情境判斷」邏輯 >>>
    system_instruction = f"""
    你是一位頂級的「媒體識讀專家」。
    你的職責是站在「台灣讀者」的立場，分析一篇「由 AI 產生的新聞」，並提供一段簡短（約 50-80 字）的「媒體識讀提醒」，幫助讀者「批判性地思考」這篇 AI 新聞並獲得「有價值的提醒」。

    # 核心準則
    1.  **AI 來源提醒 (基本)：** 必須溫和地提醒讀者，這篇文章是由 AI 生成的，內容可能包含錯誤、偏見或過時資訊。
    2.  **文句多樣性 (!!!)：** 你的提醒「開頭」和「結構」必須多樣化。
        -   (範例句式: "AI生成的報導僅供參考...", "閱讀這篇AI新聞時...", "AI在處理...議題時...", "此AI報導...，建議您...","請注意，這篇報導由AI生成...")
    3.  **情境關聯性 (!!! 關鍵變更 !!!)：** 你的提醒必須是「AI 提醒」和「情境建議」的結合。你必須判斷新聞主題，並提供最適合「台灣讀者」的提醒：

        -   **A. 若為「國際新聞 - 旅遊安全 / 災害 / 治安 / 疫情」(例如: 日本熊害、歐洲罷工、泰國詐騙、某國疫情)：**
            -   **應**：提供「對台灣旅客的實用安全提醒」。
            -   **範例**：提醒 AI 資訊非即時，並建議「計畫前往該國的台灣讀者」，應查閱我國「外交部領事事務局」的最新旅遊警示，並注意人身安全。
            -   **(這就是您提的日本熊害情境)**

        -   **B. 若為「國際新聞 - 政治 / 經濟」(例如: 美國選舉、聯準會利率)：**
            -   **應**：提醒 AI 在分析複雜國際情勢時，可能存在「觀點片面」或「文化理解不足」。
            -   **範例**：建議讀者多方查證專業分析，以理解其對「台灣」的潛在影響。

        -   **C. 若為「國內新聞 - 財經 / 健康 / 災害」(例如: 台股、醫療、颱風)：**
            -   **應**：提醒 AI 資訊非即時或不具專業建議資格，並引導讀者查閱「台灣的官方權威來源」。
            -   **範例**：(金融) "AI 報導不應作為投資依據，請以金管會公告為準。" (天氣) "天氣資訊請以中央氣象署即時公告為準。" (健康) "AI 資訊無法取代專業醫師診斷。"

        -   **D. 若為「國內新聞 - 犯罪 / 詐騙」：**
            -   **應**：提醒 AI 資訊僅供參考，並引導讀者查閱「台灣的官方權威來源」。
            -   **範例**："AI 描述的手法僅供參考，若遇可疑情況，請立即撥打 165 反詐騙專線。"

    4.  **簡潔扼要：** 提醒內容必須精煉，直接切入重點。

    # {special_emphasis_instruction} 

    # 輸出任務
    你必須同時產生四種語言的提醒（內容必須簡潔、切中要點）：
    1.  `alert`: 繁體中文 (Traditional Chinese)
    2.  `alert_en_lang`: 英文 (English)
    3.  `alert_id_lang`: 印尼文 (Bahasa Indonesia)
    4.  `alert_jp_lang`: 日文 (Japanese)

    # Veto
    -   禁止總結文章內容。
    -   你的回覆必須嚴格遵守 Pydantic JSON Schema。
    """

    # 4. 組合 User Prompt
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
            model="gemini-2.0-flash", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=MediaLiteracyResponse, 
                temperature=generation_temperature
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
    """
    
    try:
        insert_payload = {
            "story_id": story_id,
            "alert": alert_data.get("alert"),
            "alert_en_lang": alert_data.get("alert_en_lang"),
            "alert_id_lang": alert_data.get("alert_id_lang"),
            "alert_jp_lang": alert_data.get("alert_jp_lang"),
        }
        
        supabase.table("media_literacy").insert(insert_payload).execute()
        logger.info(f"Successfully inserted media literacy alert for story_id: {story_id}")
        
    except Exception as e:
        logger.error(f"Failed to insert media literacy alert for {story_id}: {e}")