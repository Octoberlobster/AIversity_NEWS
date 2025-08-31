from pydantic import BaseModel
from google.genai import types
from env import gemini_client
import Knowledge_Base
from Knowledge_Base import StoryMap

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

    def chat(self, prompt: str, categories: list[str], topic_id = None) -> list[dict]:
        """對指定分類的模型發送訊息"""
        responses = []
        for category in categories:
            Knowledge_Base.set_knowledge_base(prompt, category, topic_id)
            model = self.create_model(category)
            response = model.send_message(message=prompt)
            # loop response.parsed.news_id and change the news_id with StoryMap
            for i, news_id in enumerate(response.parsed.news_id):
                print(type(news_id))
                print(news_id)
                response.parsed.news_id[i] = StoryMap.story_map.get(news_id,news_id)
            responses.append(dict(response.parsed))  # 轉成 dict 加入回應列表
        return responses
    
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