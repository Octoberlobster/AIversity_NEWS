from pydantic import BaseModel
from google.genai import types
from env import gemini_client
import Knowledge_Base
from Knowledge_Base import StoryMap
import re

class ChatInfo(BaseModel):
    news_id: list[str]
    chat_response: str


class ChatRoom:
    def __init__(self):
        # 每個 ChatRoom 實例各自維護一份 category → model 的映射
        self.model_dict = {
            "Politics": -1,
            "Taiwan News": -1,
            "Science & Technology": -1,
            "International News": -1,
            "Lifestyle & Consumer News": -1,
            "Sports": -1,
            "Entertainment": -1,
            "Business & Finance": -1,
            "Health & Wellness": -1,
            "search": -1,
            "topic": -1,
        }

        self.model_history = {
            "Politics": [],
            "Taiwan News": [],
            "Science & Technology": [],
            "International News": [],
            "Lifestyle & Consumer News": [],
            "Sports": [],
            "Entertainment": [],
            "Business & Finance": [],
            "Health & Wellness": [],
            "search": [],
            "topic": [],
        }

    def create_model(self, category: str):
        """如果該分類還沒建立過模型，就初始化一個"""
        model_name = "gemini-2.0-flash"

        if category not in self.model_dict:
            raise ValueError(f"Unknown category: {category}")

        # 已存在則直接回傳
        if self.model_dict[category] != -1:
            self.model_history[category] = self.model_dict[category]._comprehensive_history

        # 初始化新模型
        self.model_dict[category] = gemini_client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=Knowledge_Base.get_knowledge_base(category),
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
            history=self.model_history[category]
        )
        return self.model_dict[category]

    def chat(self, prompt: str, categories: list[str], id = None) -> list[dict]:
        """對指定分類的模型發送訊息"""
        responses = []
        for category in categories:
            Knowledge_Base.set_knowledge_base(prompt, category, id)
            model = self.create_model(category)
            response = model.send_message(message=prompt)
            # loop response.parsed.news_id and change the news_id with StoryMap
            for i, news_id in enumerate(response.parsed.news_id):
                print(type(news_id))
                print(news_id)
                response.parsed.news_id[i] = StoryMap.story_map.get(news_id,news_id)
            #response.parsed.chat_response = clean_markdown_spacing(response.parsed.chat_response)
            responses.append(dict(response.parsed))  # 轉成 dict 加入回應列表
        return responses
    
# def clean_markdown_spacing(text: str) -> str:
#     # 1. 連續三個以上換行只留兩個（保留一行空白）
#     text = re.sub(r'\n{3,}', '\n\n', text)
#     # 2. 將「段內列表」前後的多餘空行去除
#     text = re.sub(r'\n\n(-|\d+\.)', r'\n\1', text)
#     # ✅ 3. 將連續兩個換行改為一個換行
#     text = re.sub(r'\n{2,}', '\n', text)
#     # 4. 去除開頭與結尾多餘空白
#     text = text.strip()
#     return text
    
# category = ["search"]
# prompt = "我想看體育新聞"
# Room = ChatRoom()
# responses = Room.chat(prompt, category)
# print(responses)


# category = ["topic"]
# prompt = "有什麼新聞看"
# Room = ChatRoom()
# response = Room.chat(prompt, category,"1e0dcbe6-36c5-4c37-bb16-55cbe7abdfa7")
# print(Room.model_dict["topic"]._comprehensive_history)

# category = ["Business & Finance"]
# prompt = "你好，自我介紹"
# Room = ChatRoom()
# response = Room.chat(prompt, category,"88690989-f9fe-42a7-aa35-81b8463eda3a")
# print(response)