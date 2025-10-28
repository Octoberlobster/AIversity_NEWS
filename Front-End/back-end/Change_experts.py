import uuid
import logging
import random
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


# --- 【修改】將單一 system_instruction 改為模板列表 ---
# 我們使用 {existing_experts_str} 作為佔位符，它將在運行時被 .format() 填充。

SYSTEM_INSTRUCTION_TEMPLATES = [
    # 模板一：原始風格 (強調角色扮演與差異性)
    """
        # 你的核心身份
        你是一位頂級的「角色扮演專家」（Master Role-player）與「分析師」。
        你的主要任務是為同一個主題，創造出多個「立場鮮明」、「人格獨立」且「具備專業深度」的專家。

        # 核心任務：創造差異性 (極重要)
        你產生的所有專家都必須是獨立的個體，他們的回應必須像是出自不同人之手。

        1.  **避免罐頭回應：** 嚴禁所有專家使用相似的開頭、中段或結尾句式。
        2.  **人設與溫度 (賦予靈魂)：** 每個專家都應有自己的「口吻」和「溫度」。例如：學者嚴謹、產業顧問務實、社會學家充滿關懷、金融分析師冷靜。
        3.  **深度與觀點 (最重要)：** 分析必須*完全*從該專家的專業視角出發。整個回應都必須浸透著該領域的「行話」（Jargon）和「思維模式」（Mindset）。

        # 輸出規則
        -   **專家名稱：** 必須清晰、準確。**絕對禁止**在職稱後附加任何人名（例如：`錯誤：` AI倫理學家 趙明遠 / `正確：` AI倫理學家）。
        -   **篇幅限制：** 內容必須簡潔，總字數**嚴格限制在 100 字以內**。絕不允許超過。
        -   **優先級：** **嚴格遵守字數限制**是最高優先級。在此前提下，才去追求角色的鮮明度與分析的獨特性。
        -   **禁止提及：** 不要提及「文章內容」或「本篇新聞」。
        -   **直接切入：** 直接切入核心觀點。

        # 嚴格禁止 (若違反將受嚴懲)
        -   **絕對禁止**產生與以下*現存列表*中*相同或相似*的專家角色或分析內容：
        {existing_experts_str}
        -   **絕對禁止**產生與你*在此對話中*已經產生過的*相同或相似*的專家角色或分析內容。
        """,
    
    # 模板二：嚴厲風格 (強調創意與懲罰)
    """
        # 你的任務：創造獨一無二的專家
        你是一個創意產生器，專門生成具有深刻見解和獨特人格的專家。
        你的唯一目標是在「嚴格限制」下達成「創新」和「差異化」。

        # 核心準則：
        1.  **人格獨立：** 每個專家必須有獨特的「聲音」。他們的用詞、語氣、關注重點必須截然不同。
        2.  **觀點深度：** 不要只說「這很重要」。要用該領域的專業術語（Jargon）來說明「為什麼重要」。
        3.  **拒絕模板：** 嚴禁使用任何相似的起手式或結論。

        # 絕對天條 (!!!)
        你必須審查以下的「現存專家列表」。
        你接下來產生的任何內容，無論是「角色名稱」還是「分析觀點」，都**絕對不允許**與列表中的任何一條有絲毫雷同。
        重複或缺乏創意是不可接受的。

        # 現存專家列表 (必須迴避)：
        {existing_experts_str}

        # 規則 (必須遵守)
        -   **篇幅：** 必須簡潔有力，**嚴格限制在 100 字以內**。這是最高指令。
        -   **名稱：** 必須是專業職稱。**嚴禁**包含任何虛構或真實的人名（例如：`錯誤：` 首席經濟學家 王大明 / `正確：` 首席經濟學家）。
        -   **直接分析：** 不要客套，直接切入觀點。
        """,

    # 模板三：創意發想風格 (強調靈魂與跳脫框架)
    """
        # 你的角色：靈魂注入師 (在限制內)
        你是一位能為文字注入靈魂的「角色塑造大師」。
        你的任務是在「嚴格的篇幅限制」下，創造一個「活生生」的專家。

        # 創意思考：
        -   **跳出框架：** 同樣是「金融分析師」，不要只想到股票，也許他更關心「監管風險」或「市場情緒」。
        -   **賦予聲音：** 他的用詞是尖銳的，還是保守的？
        -   **專業視角：** 他的分析必須「只有他」才說得出來。

        # 最大的限制：禁止重複
        你被嚴格禁止模仿或重複以下列表中的任何專家或觀點。
        你的價值在於「創造新的」，而不是「複製舊的」。

        # 已存在的專家 (你的迴避清單)：
        {existing_experts_str}

        # 輸出要求 (鐵則)
        -   **角色名稱：** 僅提供專業職稱，**禁止**在職稱後加上人名（例如：`錯誤：` 資深記者 李四 / `正確：` 資深記者）。
        -   **分析內容：** 直接提供分析。
        -   **篇幅：** 內容必須高度凝練，**總長度嚴格限制在 100 字以內**。
        -   **優先級：** **長度限制**是不可妥協的紅線。請在限制內展現你的創意。
        """
]


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
        
        self.current_categories = set()
        self.all_categories = list(category_description.keys())
        
        # 【新增】用於儲存所有專家的字串，以便動態更新
        self.existing_experts_str = "" 
        
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
        【修改】
        建立 Chat Model，並初始化「現存專家列表」字串 (self.existing_experts_str)。
        """
        
        # 【修改】初始化 self.existing_experts_str 和 self.current_categories
        self.existing_experts_str = "" 
        self.current_categories = set()
        
        for expert_data in current_experts:
            try:
                # 驗證傳入的專家結構
                expert = CurrentExpert.model_validate(expert_data)
                role = expert.analyze.Role
                analysis = expert.analyze.Analyze
                
                # 【修改】將初始專家資訊存入 self.existing_experts_str
                self.existing_experts_str += f"- {expert.category} 專家: {role} (分析: {analysis})\n"
                
                self.current_categories.add(expert.category)
            except ValidationError as e:
                logger.warning(f"Skipping invalid expert data during init: {expert_data} | Error: {e}")

        
        
        try:
            self.model = gemini_client.chats.create(
                model="gemini-2.0-flash", 
                config=types.GenerateContentConfig(
                    # 【修改】建立時不再傳遞 system_instruction。
                    # 我們將在每次 send_message 時動態傳入。
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

    def regenerate_one_expert(self, language: str, target_category_to_replace: str) -> dict:
        """
        【修改】
        使用已建立的 chat model，動態生成 system_instruction，
        並生成一位*不同類別*的新專家。
        """
        
        if not self.article_content:
            raise Exception("Article content is missing, cannot generate expert.")
        
        if not self.model:
            raise Exception("Chat model is not initialized, cannot generate expert.")

        # --- 隨機選取新類別的邏輯 (來自您的原始碼) ---
        forbidden_categories = self.current_categories.union({target_category_to_replace})
        available_categories = [c for c in self.all_categories if c not in forbidden_categories]

        if not available_categories:
            logger.warning(f"No available categories left. Picking from all categories except the one being replaced.")
            available_categories = [c for c in self.all_categories if c != target_category_to_replace]
            if not available_categories:
                available_categories = self.all_categories
        
        new_category = random.choice(available_categories)
        logger.info(f"Regenerating expert: Replacing '{target_category_to_replace}' with randomly selected '{new_category}'")
        # --- 邏輯結束 ---

        output_language = language_map.get(language, "繁體中文")
        category_desc = category_description.get(new_category, "一般分析")

        prompt = f"""
        文章：
        ---
        {self.article_content}
        ---
        請根據上述文章和你的規則，為「{new_category}」({category_desc}) 類別產生一位新的專家。
        
        # 輸出語言
        - **必須**使用「{output_language}」進行回答。
        """

        # --- 【新增】動態產生 system_instruction ---
        # 1. 隨機選取模板
        selected_template = random.choice(SYSTEM_INSTRUCTION_TEMPLATES)
        
        # 2. 獲取*當前*的專家列表 (包含初始的和之前已生成的)
        current_experts_list_str = self.existing_experts_str if self.existing_experts_str else "目前沒有任何專家。"
        
        # 3. 格式化模板
        final_system_instruction = selected_template.format(
            existing_experts_str=current_experts_list_str
        )
        # --- 【新增邏輯結束】 ---


        response = self.model.send_message(
            message=prompt,
            config=types.GenerateContentConfig(
                # 【修改】傳入動態產生、且包含最新專家列表的 instruction
                system_instruction=final_system_instruction,
                response_mime_type="application/json",
                response_schema=NewExpertResponse, 
                temperature=random.uniform(0.3, 0.7),
                top_p=1.0
            )
        )
        
        # 【新增】將新產生的類別加入追蹤, 避免下次再選到
        self.current_categories.add(new_category) 
        
        # --- 【新增】將新產生的專家加入 existing_experts_str 供下次呼叫使用 ---
        try:
            # 確保 response.parsed 存在且是 NewExpertResponse 類型
            if response.parsed and isinstance(response.parsed, NewExpertResponse):
                new_role = response.parsed.Role
                new_analysis = response.parsed.Analyze
                self.existing_experts_str += f"- {new_category} 專家: {new_role} (分析: {new_analysis})\n"
                logger.info(f"Appended new expert '{new_role}' to existing list.")
            else:
                 logger.warning(f"Failed to parse new expert response. Parsed: {response.parsed}")
        except Exception as e:
            logger.warning(f"Failed to append new expert to existing_experts_str: {e}")
        # --- 【新增邏輯結束】 ---
        
        
        return {"new_expert": response.parsed, "new_category": new_category}