import uuid
import logging
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
    "Taiwan News",
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
    "Taiwan News": "對於台灣有甚麼影響",
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
        for expert_data in current_experts:
            try:
                # 驗證傳入的專家結構
                expert = CurrentExpert.model_validate(expert_data)
                role = expert.analyze.Role
                analysis = expert.analyze.Analyze
                existing_experts_str += f"- {expert.category} 專家: {role} (分析: {analysis})\n"
            except ValidationError as e:
                logger.warning(f"Skipping invalid expert data during init: {expert_data} | Error: {e}")

        system_instruction = f"""
        你是一位專業分析產生器。你的任務是扮演一個特定領域的專家，並提供精闢的分析。

        # 核心規則 (極重要)
        - 產生的類別專家必須與文章內容和所選類別高度相關。
        - 專家名稱必須清晰、準確，避免捏造不存在的職業名稱。
        - 每個類別的分析必須符合下列要求：
          - 以該類別的專家角色進行分析
          - 精準描述對該類別的重大影響
          - 內容必須具體，總字數不超過 80 字
          - 不要提及「知識庫」、「文章內容」或「本篇新聞」等字眼
          - 請直接輸出具體影響

        # 嚴格禁止 (若違反將受嚴懲)
        - **絕對禁止**產生與以下*初始列表*中*相同或相似*的專家角色或分析內容：
        {existing_experts_str}
        - **絕對禁止**產生與你*在此對話中*已經產生過的*相同或相似*的專家角色或分析內容。
        """
        
        try:
            self.model = gemini_client.chats.create(
                model="gemini-2.0-flash", 
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=NewExpertResponse, # Gemini 回應的 Pydantic model
                ),
                history=[]
            )
        except Exception as e:
            logger.error(f"Failed to create Gemini chat model: {e}")
            self.model = None

    def regenerate_one_expert(self, language: str, target_category: str) -> NewExpertResponse:
        """
        使用已建立的 chat model，生成一位新專家。
        """
        
        if not self.article_content:
            raise Exception("Article content is missing, cannot generate expert.")
        
        if not self.model:
            raise Exception("Chat model is not initialized, cannot generate expert.")

        output_language = language_map.get(language, "繁體中文")
        category_desc = category_description.get(target_category, "一般分析")

        prompt = f"""
        文章：
        ---
        {self.article_content}
        ---
        請根據上述文章和你的規則，為「{target_category}」({category_desc}) 類別產生一位新的專家。
        
        # 輸出語言
        - **必須**使用「{output_language}」進行回答。
        """

        response = self.model.send_message(message=prompt)
        return response.parsed # 傳回 NewExpertResponse 物件
