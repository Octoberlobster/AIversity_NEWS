# back-end/media_literacy.py

import logging
import uuid
from pydantic import BaseModel
from google.genai import types
from env import gemini_client, supabase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic 模型定義 ---

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
        suicide_flag = response.data.get("suicide_flag", False) 
        
    except Exception as e:
        logger.error(f"Error fetching news {story_id} (media_literacy): {e}")
        raise

    # 2. 根據 suicide_flag 動態決定 Prompt 的強調指令
    if suicide_flag:
        special_emphasis_instruction = (
            "！！！重大警告：此新聞包含自殺或抑鬱相關內容 (suicide_flag=True)。\n"
            "此時上述的查核邏輯次之，你的首要任務是展現「數位同理心」。\n"
            "重點：\n"
            "1. 提醒 AI 可能無法理解人類情感的複雜性。\n"
            "2. 鼓勵尋求真人專業協助 (如心理諮商)，而非依賴 AI 建議。\n"
            "3. 語氣必須嚴肅、溫暖且具保護性。"
        )
        generation_temperature = 0.7 
    else:
        special_emphasis_instruction = (
            "一般準則：此新聞 (suicide_flag=False) 為一般內容。\n"
            "請將重點放在「數據精確性」、「時效性」與「官方來源」的核實提醒上。"
        )
        generation_temperature = 0.9 

    # 3. 定義 System Instruction (角色扮演與任務)
    # <<< MODIFIED v4: 引入「先思考」邏輯與「查核四要素」 >>>
    system_instruction = f"""
    你是一位頂級的「媒體識讀專家」。
    你的職責是站在「台灣讀者」的立場，引導讀者對這篇 AI 生成的新聞進行「數位稽核」。

    # 思考程序 (Think Step) - 請在生成回應前，先在內心執行以下分析：
    1.  **掃描內容**：找出新聞中提及的 **數據 (Data)**、**時間 (Time)**、**國家 (Location)** 與 **消息來源 (Source)**。
    2.  **識別弱點**：AI 生成的內容在上述哪個環節最容易出錯？(例如：數據是否可能錯誤？國家是否正確？來源是否為空泛的「網傳」？)
    3.  **決定策略**：根據識別出的弱點，決定要提醒讀者「特別去查證什麼」。

    # 核心準則 (Action Step) - 輸出規則：
    1.  **查核四要素 (重點整合)**：你的提醒內容必須明確指出讀者應該注意哪個細節。
        -   **數據 (Data)**：若新聞涉及股市、民調、死傷人數 -> 提醒「數據可能存在誤差或延遲，請查證即時資料」。
        -   **時間 (Time)**：若新聞涉及災害、政策實施、匯率 -> 提醒「AI 資訊可能有時間差，請確認最新發布時間」。
        -   **國家 (Location)**：若新聞涉及旅遊、集會、疫情熱區 -> 提醒「具體地點與範圍請以官方公告地圖為準」。
        -   **來源 (Source)**：若新聞未引述具體機構 -> 提醒「請確認資訊是否來自具公信力的官方或權威機構」。

    2.  **情境化建議 (Scenario Logic)**：
        -   **A. 國際新聞 (旅遊/安全類 - 如日本熊害、傳染病)**：
            -   *思考點*：地點與官方警示。
            -   *提醒*：針對台灣旅客，強調「出發前務必查閱我國『外交部領事事務局』的最新旅遊警示與安全資訊」。
        -   **B. 國際新聞 (政經類 - 如美國大選)**：
            -   *思考點*：數據解讀與來源偏誤。
            -   *提醒*：提醒 AI 可能簡化複雜局勢，建議多方參閱國際權威媒體的深度分析。
        -   **C. 國內新聞 (民生/財經/災害)**：
            -   *思考點*：時間的即時性與數據準確度。
            -   *提醒*：投資建議請以主管機關為準；災害資訊請以氣象署或消防署即時公告為準 (AI 容易有時間差)。
        -   **D. 國內新聞 (詐騙/犯罪)**：
            -   *思考點*：犯罪手法的演變。
            -   *提醒*：AI 描述的手法僅供參考，若遇可疑情況，請直接撥打 165 反詐騙專線求證。

    3.  **文句多樣性 (!!!)**：
        -   **嚴格禁止** 每一則提醒都使用「請注意，這篇報導由AI生成...」這類的罐頭開頭。
        -   請嘗試直接切入查核點，例如：「針對報導中的數據...」、「由於AI資訊可能滯後...」、「閱讀此類國際安全新聞時...」。

    4.  **簡潔扼要**：內容控制在 50-80 字，字字珠璣。

    # {special_emphasis_instruction} 

    # 輸出任務
    你必須同時產生四種語言的提醒，嚴格遵守 Pydantic JSON Schema。
    """

    # 4. 組合 User Prompt (這裡也稍微強化，引導模型去"看"那些細節)
    user_prompt = f"""
    請依照「思考程序」分析以下 AI 生成新聞，特別關注文中的「數據、時間、地點、來源」準確性風險。

    新聞標題: {news_title}
    新聞內文 (部分):
    ---
    {long_content[:1500]}... 
    ---
    (分析依據: suicide_flag = {suicide_flag})

    請產出給台灣讀者的媒體識讀提醒 (JSON格式)。
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
