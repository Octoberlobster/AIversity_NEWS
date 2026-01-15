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
        # ... (init remains the same) ...
        self.model_dict = {
            "Politics": -1,
            "Taiwan News": -1,
            "Science & Technology": -1,
            "International News": -1,
            "Lifestyle & Consumer": -1,
            "Sports": -1,
            "Entertainment": -1,
            "Business & Finance": -1,
            "Health & Wellness": -1,
            "search": -1,
        }
        self.model_history = { # Initialize history for potential dynamic categories too
             "Politics": [],
             "Taiwan News": [],
             "Science & Technology": [],
             "International News": [],
             "Lifestyle & Consumer": [],
             "Sports": [],
             "Entertainment": [],
             "Business & Finance": [],
             "Health & Wellness": [],
             "search": [],
         }


    def create_model(self, category: str, language: str = "zh-TW"): # <<< MODIFIED
        """如果該分類還沒建立過模型，就初始化一個"""
        model_name = "gemini-2.0-flash"

        # Allow dynamic categories if not 'search'
        if category != "search" and category not in self.model_dict:
             self.model_dict[category] = -1
             self.model_history[category] = []
        elif category not in self.model_dict:
             raise ValueError(f"Unknown category: {category}")


        # 已存在則直接回傳
        if self.model_dict[category] != -1:
            # Sync history before returning existing model
            self.model_history[category] = self.model_dict[category]._comprehensive_history

        # 初始化新模型 (ensure history exists for the category)
        self.model_dict[category] = gemini_client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=Knowledge_Base.get_knowledge_base(category, language), # <<< MODIFIED
                response_mime_type="application/json",
                response_schema=ChatInfo if category == "search" else Knowledge_Base.NewExpertResponse, # Use correct schema
            ),
             history=self.model_history.get(category, []) # Use .get with fallback
        )
        return self.model_dict[category]


    # <<< MODIFIED: Function signature >>>
    def chat(self, prompt: str, categories_data: list[dict], id = None, topic_flag = False, language: str = "zh-TW") -> list[dict]:
        """對指定分類的模型發送訊息。 categories_data is a list of dicts like [{'category': 'Politics', 'role': '政治分析師', 'analyze': '分析...'}]"""
        responses = []
        for expert_data in categories_data:
            category = expert_data.get('category')
            role = expert_data.get('role')     # Extract role
            analyze = expert_data.get('analyze') # Extract analyze

            if not category:
                continue

            # <<< MODIFIED: Pass role and analyze >>>
            Knowledge_Base.set_knowledge_base(prompt, category, id, topic_flag, language, role=role, analyze=analyze)

            model = self.create_model(category, language) # Pass language
            response = model.send_message(message=prompt)

            # Process response based on category
            if category == "search":
                 # Process search response (including StoryMap mapping)
                 for i, news_id in enumerate(response.parsed.news_id):
                     print(type(news_id))
                     print(news_id)
                     response.parsed.news_id[i] = StoryMap.story_map.get(str(news_id), news_id) # Ensure key is string
                 responses.append(dict(response.parsed))
            else:
                 # Process expert response (Role/Analyze format expected from NewExpertResponse schema)
                 # We need to structure the response like ChatInfo for consistency if needed by frontend
                 expert_response_data = {
                      "news_id": [], # Expert responses don't typically return news_ids directly this way
                      "chat_response": f"**{response.parsed.Role}：**\n\n{response.parsed.Analyze}" # Format the response
                 }
                 responses.append(expert_response_data)


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