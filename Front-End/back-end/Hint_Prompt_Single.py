from pydantic import BaseModel
from functools import lru_cache
from google.genai import types
from env import gemini_client
import os

class HintPromptResponse(BaseModel):
    Hint_Prompt: list[str]


# @lru_cache(maxsize=128)
# def generate_hint_prompt(option,article,chat_content):
#     response = gemini_client.models.generate_content(
#         model="gemini-2.0-flash",
#         contents= f"使用者當前想跟{option}領域的專家(們)聊天，請根據{article}，生成 4 個最合適且能幫助使用者開始聊天的提示詞。",
#         config=types.GenerateContentConfig(
#             system_instruction=(
#                 "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
#                 "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字"
#                 f"使用者正在閱讀的文章是：{article}，"
#                 f"使用者當前的聊天內容是：{chat_content}，"
#                 "每個提示字請務必確保與文章內容相關，並且能夠引導使用者進行深入的討論。"
#             ),
#             response_mime_type="application/json",
#             response_schema=HintPromptResponse,
#         ),
#     )
#     return dict(response.parsed)

# def refresh_hint_prompt():
#     generate_hint_prompt.cache_clear()



class Hint_Prompt_Single:
    def __init__(self,chat_content):
        self.chat_content = chat_content

    @staticmethod
    @lru_cache(128)
    def generate_hint_prompt(option, article, chat_content):
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents= f"使用者當前想跟{option}領域的專家(們)聊天，生成1至2個最合適且能幫助使用者開始聊天的提示詞。",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "你是一位給予提示詞的助手，主要目的是幫助使用者開始聊天。"
                    "並且為了減輕使用者負擔，每個提示詞都不應該超過10個字"
                    f"使用者正在閱讀的文章是：{article}，"
                    f"使用者的聊天紀錄：{chat_content}，"
                    "每個提示字請務必確保與文章內容相關，並且能夠引導使用者進行深入的討論。"
                    "除此之外，你會接收到使用者的聊天紀錄，請根據使用者的聊天紀錄來生成更進一步的提示詞。"
                ),
                response_mime_type="application/json",
                response_schema=HintPromptResponse,
            ),
        )
        return dict(response.parsed)
    
    def refresh_hint_prompt(self):
        self.generate_hint_prompt.cache_clear()

    def append_to_chat_content(self, new_content):
        self.chat_content += new_content

#test in terminal
# option = ['政治', '財經']
# generator = Hint_Prompt_Single("")
# article = "台灣首波針對25位國民黨立委及新竹市長高虹安的大罷免行動於7月26日落幕，25案全數未通過。民進黨秘書長林右昌為此承擔責任，已於27日向黨主席賴清德請辭。此次罷免結果引發各界反思，部分評論指出民進黨的「抗中保台」招牌在地方選舉中似乎效力減弱。\n\n罷免結果出爐後，林右昌在臉書上表示，身為執政黨，民進黨責無旁貸，任何做得不夠好的地方都應由他承擔，並對罷免團體志工的熱情和愛台灣的精神表達敬佩。林右昌的妻子吳秋英在臉書發文表達對丈夫的支持，林右昌的妹妹也表示「辭了也好」，認為林右昌為黨付出許多。\n\n多位學者和政治評論員針對此次罷免結果發表看法。部分人士認為，民進黨的「抗中保台」論述在地方選舉中未能有效說服選民，尤其年輕族群更關心民生議題，如高房價、低薪和兵役問題。此外，也有聲音認為，行政團隊的施政效率和回應民意的能力也是影響選民投票意向的關鍵因素。\n\n此次罷免行動也引發美國學者關注，認為台灣政治兩極化日益嚴重，對國家安全造成危害，朝野政黨應尋求妥協。部分學者則認為，台灣內部政治鬥爭恐影響其應對北京壓力和處理台美關係的能力。\n\n雖然此次大罷免未能成功，但部分人士認為，此結果有助於避免大罷免成為常態，對台灣民主制度的發展有正面意義。賴清德總統則感謝公民力量，並表示執政團隊將更審慎反思社會的反應。\n\n第二波針對7位國民黨立委的罷免案將於8月23日舉行，屆時投票結果將再次牽動台灣政局。"
# response = generator.generate_hint_prompt(tuple(option), article, generator.chat_content)
# print(response)
# option = ['科技', '健康']
# response = generator.generate_hint_prompt(tuple(option), article, generator.chat_content)
# print(response)
# print("------")
# #應該要是快取內容
# option = ['政治', '財經']
# response = generator.generate_hint_prompt(tuple(option), article, generator.chat_content)
# print(response)
# print("------")
# generator.refresh_hint_prompt()
# response = generator.generate_hint_prompt(tuple(option), article, generator.chat_content)
# print(response)
# print("------")
# print(type(response))