from pydantic import BaseModel
from google.genai import types
from env import gemini_client
import Knowledge_Base

#TODO : 修改model_dict只有9個領域，增加專題的model與首頁搜尋的model

class ChatInfo(BaseModel):
    name: str
    chat_response: str
    related_news: list[str]


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
        }

    def create_model(self, category: str):
        """如果該分類還沒建立過模型，就初始化一個"""
        model_name = "gemini-2.0-flash"

        if category not in self.model_dict:
            raise ValueError(f"Unknown category: {category}")

        # 已存在則直接回傳
        if self.model_dict[category] != -1:
            return self.model_dict[category]

        # 初始化新模型
        self.model_dict[category] = gemini_client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=Knowledge_Base.get_knowledge_base(category),
                response_mime_type="application/json",
                response_schema=ChatInfo,
            ),
        )
        return self.model_dict[category]

    def chat(self, prompt: str, categories: list[str]):
        """對指定分類的模型發送訊息"""
        responses = []
        for category in categories:
            model = self.create_model(category)
            response = model.send_message(message=prompt)
            responses.append(dict(response.parsed))  # 轉成 dict 加入回應列表
        return responses