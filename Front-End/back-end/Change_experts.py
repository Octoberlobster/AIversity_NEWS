import uuid
import logging
import random  # <-- 【新增】導入 random
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Literal
from google.genai import types
from env import gemini_client, supabase

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic 模型定義 ---

# 複用 Pro_Analyze.py 中的定義
categories = Literal[
    "Politics",
    "International News",
    "Science & Technology",
    "Lifestyle & Consumer",
    "Sports",
    "Entertainment",
    "Business & Finance",
    "Health & Wellness",
]

class AnalyzeItem(BaseModel):
    Role: str
    Analyze: str

class CurrentExpert(BaseModel):
    analyze_id: str
    category: str
    analyze: AnalyzeItem

class ExpertToRegenerate(BaseModel):
    analyze_id: str
    category: str

# Gemini 回應的 Schema
class NewExpertResponse(BaseModel):
    Role: str
    Analyze: str

# --- 語言和類別對照表 ---

language_map = {
    "zh-TW": "繁體中文",
    "en-US": "English",
    "ja-JP": "日本語",
    "id-ID": "Bahasa Indonesia"
}

# 從 Pro_Analyze.py 複製
category_description = {
    "Politics": "對於台灣的政治有甚麼影響",
    "International News": "對於國際上有甚麼影響",
    "Science & Technology": "科學研究、太空探索、生物科技、AI、大數據、半導體、電子產品、電玩遊戲、網安等科技發展",
    "Lifestyle & Consumer": "旅遊、時尚、飲食、消費趨勢等",
    "Sports": "體育賽事、運動員動態、奧運、世界盃等",
    "Entertainment": "電影、音樂、藝人新聞、流行文化等",
    "Business & Finance": "對於台灣的經濟有什麼影響",
    "Health & Wellness": "公共衛生、醫學研究、醫療技術等",
}


# --- 核心功能類別 ---

class ExpertRegenerator:
    def __init__(self, current_experts: List[Dict[str, Any]], story_id: str):
        """
        初始化專家生成器。
        在建立時即獲取文章內容並建立一個有記憶的 chat model。
        """
        self.model = None
        self.story_id = story_id
        self.article_content = self._get_article(story_id)
        if not self.article_content:
            logger.error(f"Failed to fetch article for story_id: {story_id}. Expert generation will fail.")
        
        self.current_categories = set() # <-- 【新增】追蹤目前有哪些類別
        self.all_categories = list(category_description.keys()) # <-- 【新增】所有可用類別
        
        self._create_model(current_experts)

    def _get_article(self, story_id: str) -> str:
        """從 Supabase 獲取文章內容"""
        if not story_id:
            return ""
        try:
            article_response = supabase.table("single_news").select("long").eq("story_id", story_id).execute()
            if not article_response.data:
                logger.warning(f"No article found for story_id: {story_id}")
                return ""
            return article_response.data[0]["long"]
        except Exception as e:
            logger.error(f"Failed to get article {story_id}: {e}")
            return ""

    def _create_model(self, current_experts: List[Dict[str, Any]]):
        """
        根據當前專家列表，建立一個 Chat Model。
        System Instruction 會固定，Gemini 會透過 History 記住新產生的專家。
        """
        
        existing_experts_str = ""
        self.current_categories = set() # <-- 【修改】初始化
        for expert_data in current_experts:
            try:
                # 驗證傳入的專家結構
                expert = CurrentExpert.model_validate(expert_data)
                role = expert.analyze.Role
                analysis = expert.analyze.Analyze
                existing_experts_str += f"- {expert.category} 專家: {role} (分析: {analysis})\n"
                self.current_categories.add(expert.category) # <-- 【新增】將初始類別加入 set
            except ValidationError as e:
                logger.warning(f"Skipping invalid expert data during init: {expert_data} | Error: {e}")

        system_instruction = f"""
        # 你的核心身份
        你是一位頂級的「角色扮演專家」（Master Role-player）與「分析師」。
        你的主要任務是為同一個主題，創造出多個「立場鮮明」、「人格獨立」且「具備專業深度」的專家。

        # 核心任務：創造差異性 (極重要)
        你產生的所有專家都必須是獨立的個體，他們的回應必須像是出自不同人之手。

        1.  **避免罐頭回應：** - 嚴禁所有專家使用相似的開頭、中段或結尾句式。
            - 他們的用詞、語氣和句子結構必須有顯著差異。

        2.  **人設與溫度 (賦予靈魂)：** - 每個專家都應有自己的「口吻」和「溫度」。
            - 例如：學者可能嚴謹、引用數據；產業顧問可能務實、直指痛點；社會學家可能充滿人文關懷；金融分析師可能冷靜、關注風險。
            - **你必須為每個專家賦予一個獨特的「聲音」。**

        3.  **深度與觀點 (最重要)：** - 分析必須*完全*從該專家的專業視角出發。
            - **錯誤示範 (模板化)：** 「這件事影響很大，...，...，這會影響到 [領域A]。 」
            - **正確示範 (沉浸式)：** 「[領域A] 的核心指標 [指標X] 將首當其衝。我擔心的是它觸發的 [領域A的連鎖效應Y]...」
            - 整個回應都必須浸透著該領域的「行話」（Jargon）和「思維模式」（Mindset）。

        # 輸出規則
        -   **專家名稱：** 必須清晰、準確，避免捏造不存在的職業名稱。
        -   **篇幅限制：** 內容必須具體，總字數*盡量*控制在 100 字左右。（我們放寬 20 字以容納「人設」）
        -   **優先級：** **角色的鮮明度**與**分析的獨特性**，比嚴格遵守字數限制更重要。
        -   **禁止提及：** 不要提及「知識庫」、「文章內容」或「本篇新聞」等字眼。
        -   **直接切入：** 回應應直接切入該專家的核心觀點，不要有太多客套話或前言。

        # 嚴格禁止 (若違反將受嚴懲)
        -   **絕對禁止**產生與以下*初始列表*中*相同或相似*的專家角色或分析內容：
        {existing_experts_str}
        -   **絕對禁止**產生與你*在此對話中*已經產生過的*相同或相似*的專家角色或分析內容。
        """
        
        try:
            self.model = gemini_client.chats.create(
                model="gemini-2.0-flash", 
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=NewExpertResponse, # Gemini 回應的 Pydantic model
                    temperature=0.9,
                    top_p=1.0
                ),
                history=[]
            )
        except Exception as e:
            logger.error(f"Failed to create Gemini chat model: {e}")
            self.model = None

    def regenerate_one_expert(self, language: str, target_category_to_replace: str) -> dict: # <-- 【修改】回傳類型
        """
        使用已建立的 chat model，生成一位*不同類別*的新專家。
        """
        
        if not self.article_content:
            raise Exception("Article content is missing, cannot generate expert.")
        
        if not self.model:
            raise Exception("Chat model is not initialized, cannot generate expert.")

        # --- 【新增】隨機選取新類別的邏輯 ---
        # 1. 建立禁用列表 (包含所有已存在的 + 剛剛被換掉的)
        #    我們也把 chat history 中新產生的類別加入 (雖然 self.current_categories 應該已經做了)
        forbidden_categories = self.current_categories.union({target_category_to_replace})
        
        # 2. 找出所有可用的類別
        available_categories = [c for c in self.all_categories if c not in forbidden_categories]

        # 3. (Edge Case) 如果可用類別為空 (例如已產生 9 個專家)
        if not available_categories:
            logger.warning(f"No available categories left. Picking from all categories except the one being replaced.")
            available_categories = [c for c in self.all_categories if c != target_category_to_replace]
            # (Ultimate Edge Case) 如果連這樣都找不到 (例如總共只有1個類別)
            if not available_categories:
                available_categories = self.all_categories
        
        # 4. 隨機選一個新類別
        new_category = random.choice(available_categories)
        logger.info(f"Regenerating expert: Replacing '{target_category_to_replace}' with randomly selected '{new_category}'")
        # --- 【新增邏輯結束】 ---

        output_language = language_map.get(language, "繁體中文")
        category_desc = category_description.get(new_category, "一般分析") # <-- 【修改】使用 new_category

        prompt = f"""
        文章：
        ---
        {self.article_content}
        ---
        請根據上述文章和你的規則，為「{new_category}」({category_desc}) 類別產生一位新的專家。
        
        # 輸出語言
        - **必須**使用「{output_language}」進行回答。
        """

        response = self.model.send_message(message=prompt)
        
        # 【新增】將新產生的類別加入追蹤, 避免下次再選到
        self.current_categories.add(new_category) 
        
        # 【修改】回傳 Pydantic 物件和新類別的名稱
        return {"new_expert": response.parsed, "new_category": new_category}