import uuid
import logging
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any, Literal
from google.genai import types
from env import gemini_client, supabase
import json

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic 模型定義 ---

# 複用 Pro_Analyze_Topic.py 中的定義
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

# 從 Pro_Analyze_Topic.py 複製
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

class TopicExpertRegenerator:
    def __init__(self, current_experts: List[Dict[str, Any]], topic_id: str):
        """
        初始化專題專家生成器。
        在建立時即獲取完整的專題資料並建立一個有記憶的 chat model。
        """
        self.model = None
        self.topic_id = topic_id
        # 獲取完整的專題資料字串 (基於 Pro_Analyze_Topic.py 步驟 1-5)
        self.topic_data_string = self._get_topic_data_string(topic_id)
        if not self.topic_data_string:
            logger.error(f"Failed to fetch topic data for topic_id: {topic_id}. Expert generation will fail.")
        
        self._create_model(current_experts)

    def _get_topic_data_string(self, topic_id: str) -> str:
        """
        從 Supabase 獲取專題的完整階層式資料 (複製 Pro_Analyze_Topic.py 步驟 1-5)，
        並組裝成一個字串。
        """
        if not topic_id:
            return ""
        try:
            # 1️⃣ 取得專題內容
            topic_long_response = (
                supabase.table("topic")
                .select("topic_id, topic_long")
                .eq("topic_id", topic_id)
                .execute()
            )
            if not topic_long_response.data:
                 logger.warning(f"No topic found for topic_id: {topic_id}")
                 return ""
            topic_content = topic_long_response.data[0]["topic_long"]

            # 2️⃣ 取得專題分支
            topic_branches_response = (
                supabase.table("topic_branch")
                .select("topic_branch_id, topic_id, topic_branch_title, topic_branch_content")
                .eq("topic_id", topic_id)
                .execute()
            )
            topic_branches = topic_branches_response.data
            topic_branch_ids = [b["topic_branch_id"] for b in topic_branches]

            # 3️⃣ 分支與新聞的對應關係
            topic_branchs_news_stories_id_response = (
                supabase.table("topic_branch_news_map")
                .select("topic_branch_id, story_id")
                .in_("topic_branch_id", topic_branch_ids)
                .execute()
            )
            topic_branchs_news_stories_id = topic_branchs_news_stories_id_response.data

            # 4️⃣ 查詢所有相關新聞內容
            story_ids = [i["story_id"] for i in topic_branchs_news_stories_id]
            stories = []
            if story_ids: # 只有在有關聯 story_ids 時才查詢
                stories_response = (
                    supabase.table("single_news")
                    .select("story_id, news_title, short")
                    .in_("story_id", story_ids)
                    .execute()
                )
                stories = stories_response.data
            
            # 5️⃣ 組装完整階層式專題資料
            topic_data = {
                "topic_id": topic_id,
                "topic_description": topic_content,
                "branches": [],
            }

            for branch in topic_branches:
                branch_id = branch["topic_branch_id"]
                related_news = [
                    story
                    for story in stories
                    if story["story_id"]
                    in [
                        mapping["story_id"]
                        for mapping in topic_branchs_news_stories_id
                        if mapping["topic_branch_id"] == branch_id
                    ]
                ]

                topic_data["branches"].append(
                    {
                        "branch_id": branch_id,
                        "branch_title": branch["topic_branch_title"],
                        "branch_content": branch["topic_branch_content"],
                        "news": [
                            {
                                "story_id": n["story_id"],
                                "title": n["news_title"],
                                "summary": n["short"],
                            }
                            for n in related_news
                        ],
                    }
                )
            
            # (新步驟) 將組裝好的資料轉換為易讀的字串
            data_string = f"專題描述: {topic_data['topic_description']}\n\n"
            data_string += "專題分支與相關新聞:\n"
            
            if not topic_data["branches"]:
                data_string += "(此專題無分支事件)\n"
            
            for i, branch in enumerate(topic_data["branches"]):
                data_string += f"--- 分支 {i+1} ---\n"
                data_string += f"分支標題: {branch['branch_title']}\n"
                data_string += f"分支內容: {branch['branch_content']}\n"
                data_string += "相關新聞摘要:\n"
                if not branch['news']:
                     data_string += "(此分支無相關新聞)\n"
                for j, news in enumerate(branch['news']):
                    data_string += f"  - 新聞 {j+1}: {news['title']} ({news['summary']})\n"
                data_string += "\n"
                
            return data_string

        except Exception as e:
            logger.error(f"Failed to get topic data {topic_id}: {e}")
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

        # 系統提示詞 (與 Change_experts.py 相同)
        system_instruction = f"""
        你是一位專業分析產生器。你的任務是扮演一個特定領域的專家，並提供精闢的分析。

        # 核心規則 (極重要)
        - 產生的類別專家必須與文章內容和所選類別高度相關。
        - 專家名稱必須清晰、準確，避免捏造不存在的職業名稱。
        - 每個類別的分析必須符合下列要求：
          - 以該類別的專家角色進行分析
          - 精準描述對該類別的重大影響
          - 內容必須具體，總字數不超過 80 字
          - 不要提及「知識庫」、「文章內容」、「專題資料」或「本篇新聞」等字眼
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
        
        if not self.topic_data_string:
            raise Exception("Topic data string is missing, cannot generate expert.")
        
        if not self.model:
            raise Exception("Chat model is not initialized, cannot generate expert.")

        output_language = language_map.get(language, "繁體中文")
        category_desc = category_description.get(target_category, "一般分析")

        prompt = f"""
        專題資料：
        ---
        {self.topic_data_string}
        ---
        請根據上述「專題資料」和你的規則，為「{target_category}」({category_desc}) 類別產生一位新的專家。
        
        # 輸出語言
        - **必須**使用「{output_language}」進行回答。
        """

        response = self.model.send_message(message=prompt)
        return response.parsed # 傳回 NewExpertResponse 物件