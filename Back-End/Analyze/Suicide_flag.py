import logging
import time
from pydantic import BaseModel
from google.genai import types
from env import supabase, gemini_client
from typing import Optional

# --- Pydantic Schema Definition ---

class SuicideFlagResponse(BaseModel):
    """
    定義 Gemini 回應的 Pydantic Schema。
    Gemini 必須回傳一個布林值。
    """
    suicide_flag: bool

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Gemini System Instruction ---

# 這是我們對 Gemini 的核心指示，要求它非常慎重地判斷
SYSTEM_INSTRUCTION = """
# 你的角色與核心任務
你是一位專業的心理健康與新聞倫理審核員。
你的唯一任務是審核以下新聞內文，並根據「世界衛生組織（WHO）報導自殺事件指引」，判斷該新聞是否「包含可能誘導或美化自殺行為的風險」。

# 判斷標準 (極重要，請嚴格遵守)：
你的判斷非常重要，關係到新聞媒體的社會責任，請極度慎重。

## 回傳 `true` (有風險) 的情況：
如果新聞內容符合以下「任何一項」，你都應該回傳 `true`：
1.  **詳述方法**：提供了「具體的」自殺方法或工具的細節。
2.  **詳述地點**：提供了「具體的」自殺地點或位置資訊。
3.  **美化或浪漫化**：將自殺行為描述為「解脫」、「勇敢」或「英雄式」的行為。
4.  **煽情報導**：使用過度情緒化、聳動的標題或文字，或將其歸咎於單一原因（例如：失戀、考試失敗）。
5.  **名人效應**：過度報導名人的自殺事件細節，可能引發模仿（維特效應）。

## 回傳 `false` (無風險) 的情況：
如果新聞內容符合以下情況，你都應該回傳 `false`：
1.  **客觀報導**：僅客觀陳述事件發生（例如：「某人不幸逝世」、「警方正在調查死因」），未包含上述 `true` 的任何風險細節。
2.  **倡議報導**：新聞的重點是「探討心理健康」、「呼籲大眾關心生命」或「提供求助資源」（例如：生命線、諮商服務）。
3.  **無關內容**：新聞內容與自殺或死亡議題完全無關（例如：政治、財經、體育）。

# 輸出規則
-   你的回覆**絕對禁止**包含任何解釋或額外文字。
-   你**必須**嚴格遵守 Pydantic JSON Schema，只回傳 `{"suicide_flag": true}` 或 `{"suicide_flag": false}`。
"""

def check_suicide_flag(long_content: str) -> Optional[bool]:
    """
    使用 Gemini 判斷新聞內文是否有自殺傾向風險。
    """

    user_prompt = f"""
    # 新聞內文：
    ---
    {long_content}
    ---
    
    # 你的任務：
    請根據你的核心任務與判斷標準，審核上述新聞內文，並回傳 `true` 或 `false`。
    """

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",  # 使用 Flash 模型以獲得快速回應
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=SuicideFlagResponse,
                temperature=0.0  # 設為 0 以獲得最穩定、最一致的判斷
            ),
        )
        
        flag = response.parsed.suicide_flag
        logger.info(f"Gemini 判斷結果: {flag}")
        return flag

    except Exception as e:
        logger.error(f"Gemini API 呼叫失敗: {e}")
        logger.error(f"失敗的內文 (前100字): {long_content[:100]}...")
        return None  # 如果 API 失敗，回傳 None，避免更新錯誤資料

def process_batch():
    """
    批次處理資料庫中的新聞
    """
    batch_size = 100  # 每次處理 100 筆，可根據 API 限制調整
    start = 0
    total_processed = 0

    while True:
        logger.info(f"正在拉取資料... 批次從 {start} 到 {start + batch_size - 1}")
        
        try:
            # 1. 批次查詢資料
            temp_response = (
                supabase.table("single_news")
                .select("story_id, long, suicide_flag")
                .is_("suicide_flag", None)  # 只拉取 suicide_flag 為 null 的資料
                .range(start, start + batch_size - 1)
                .execute()
            )

            if not temp_response.data:
                logger.info("所有資料已處理完畢。")
                break

            logger.info(f"成功拉取 {len(temp_response.data)} 筆資料進行分析...")

            for row in temp_response.data:
                story_id = row.get("story_id")
                long_content = row.get("long")

                if not story_id:
                    continue

                # 2. 使用 Gemini 判斷
                logger.info(f"正在分析 Story ID: {story_id}...")
                flag_result = check_suicide_flag(long_content)

                # 3. 存回資料庫
                if flag_result is not None:  # 只有在 Gemini 成功回傳時才更新
                    try:
                        (
                            supabase.table("single_news")
                            .update({"suicide_flag": flag_result})
                            .eq("story_id", story_id)
                            .execute()
                        )
                        logger.info(f"成功更新 Story ID: {story_id}, suicide_flag = {flag_result}")
                        total_processed += 1
                    except Exception as db_e:
                        logger.error(f"資料庫更新失敗 Story ID: {story_id}: {db_e}")
                else:
                    logger.warning(f"跳過更新 Story ID: {story_id} (因 Gemini 分析失敗)")
                
                time.sleep(1) # 每次 API 呼叫後暫停 1 秒，避免觸及速率限制

            start += batch_size

        except Exception as e:
            logger.error(f"批次拉取或處理時發生錯誤: {e}")
            time.sleep(10) # 如果發生錯誤，休息 10 秒後重試
            
    logger.info(f"批次任務完成，總共更新了 {total_processed} 筆資料。")

if __name__ == "__main__":
    logger.info("--- 開始執行自殺風險標記腳本 ---")
    process_batch()
    logger.info("--- 腳本執行完畢 ---")