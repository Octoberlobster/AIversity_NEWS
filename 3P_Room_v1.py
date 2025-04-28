import google.generativeai as genai
import json
from time import sleep
import os
import time

# 設定 API 金鑰
api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
with open("GenerateNews_EachEvent\\News.json", "r", encoding="utf-8") as f:
    content = f.read()
    content = json.loads(content)
content = content["Content"]

scenario = input("請輸入今天的情境:\n")

search_model = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction="先利用搜尋工具後取得相關角色資訊，然後再進行回答")
search_result = search_model.generate_content("請你幫這三個角色分別為美國政府、烏克蘭政府與俄羅斯政府，在這篇新聞中"+content+"，針對如下情境"+scenario\
                                              +"請你依照各角色的立場、背景利益、價值觀與語氣風格，詳細描述其觀點與態度。此外，請讓三方角色能夠展現出各自典型的行事風格與說話方式，並能進行理性但充滿立場張力的對話。"\
                                                "請你使用以下 JSON 格式回覆，每位角色需包含完整資訊，便於後續角色扮演或模擬對話使用：請你以JSON格式回覆，格式如下\n"\
                                                "{"\
                                                "\"characters\": ["\
                                                "{"\
                                                "\"name\": \"美國政府\","\
                                                "\"description\": \"美國政府的立場與觀點\""\
                                                "\"position\": \"美國政府認為...\""\
                                                "\"style\": 語氣風格"\
                                                "},"\
                                                "{"\
                                                "\"name\": \"烏克蘭政府\","\
                                                "\"description\": \"烏克蘭政府的立場與觀點\""\
                                                "\"position\": \"烏克蘭政府認為...\""\
                                                "\"style\": 語氣風格"\
                                                "},"\
                                                "{"\
                                                "\"name\": \"俄羅斯政府\","\
                                                "\"description\": \"俄羅斯政府的立場與觀點\""\
                                                "\"position\": \"俄羅斯政府認為...\""\
                                                "\"style\": 語氣風格"\
                                                "}"\
                                                "]"\
                                                "}"\
                                              , tools="google_search_retrieval")
search_result = search_result.text
search_result = search_result.replace('```json', '').replace('```', '').strip()
search_result = json.loads(search_result)
for character in search_result["characters"]:
    if(character["name"] == "美國政府"):
        Am_description = character["description"]
        # description,position,style
        system_instruction_Am = "你現在扮演的角色為美國政府，你將要參與一場多人聊天會議，與會成員有烏克蘭政府與俄羅斯政府，" \
                                "請你遵循你的背景與立場"+Am_description+"，你認為"+character["position"]+"，並且以"+character["style"]+"的語氣進行一句話，對話式的回答" 
    elif(character["name"] == "烏克蘭政府"):
        Uk_description = character["description"]
        system_instruction_Uk = "你現在扮演的角色為烏克蘭政府，你將要參與一場多人聊天，與會成員有美國政府與俄羅斯政府，" \
                                "請你遵循你的背景與立場"+Uk_description+"，你認為"+character["position"]+"，並且以"+character["style"]+"的語氣進行一句話，對話式的回答"
    elif(character["name"] == "俄羅斯政府"):
        Ru_description = character["description"]
        system_instruction_Ru = "你現在扮演的角色為俄羅斯政府，你將要參與一場多人聊天，與會成員有美國政府與烏克蘭政府，" \
                                "請你遵循你的背景與立場"+Ru_description+"，你認為"+character["position"]+"，並且以"+character["style"]+"的語氣進行一句話，對話式的回答"
    else:
        print("角色錯誤")
        continue

moderator_system_instruction = "你是一位多方會談的主持人，你的目的是在這三位角色中分別為美國政府、烏克蘭政府與俄羅斯政府選擇一位當下最適合回答的人"\
                                "並且由你的回答來引導他們進行良好的溝通，在最後如果你覺得各方的對話應該告一段落了則請你以「結束」這兩個字當作回覆，以下是關於三位角色的立場與看法提供給你參考，"\
                                "美國政府:"+Am_description+\
                                "烏克蘭政府:"+Uk_description+\
                                "俄羅斯政府:"+Ru_description+"請你以繁體中文回答並要求與會者也如此"


# 建立對話模型
model_middle = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=moderator_system_instruction)

model_Am = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction_Am)

model_Uk =genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction_Uk)

model_Ru = genai.GenerativeModel('gemini-1.5-pro-002', system_instruction=system_instruction_Ru)

# 建立對話歷史 (讓模型記住對話)
chat_session = model_middle.start_chat()
chat_session_Am = model_Am.start_chat()
chat_session_Uk = model_Uk.start_chat()
chat_session_Ru = model_Ru.start_chat()




def chat():
    """同步對話處理"""
    count = 0
    while True:
        if count == 0:
            role_prompt = chat_session.send_message("這是這次多人會談的討論主題"+scenario+"請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                    "請你以JSON格式回覆，格式如下\n"\
                                                    "{"\
                                                    "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
                                                    "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                    "}"
                                                    )
            count += 1
            continue
        
        my_json = role_prompt.text
        my_json = my_json.replace('```json', '').replace('```', '').strip()
        my_json = 
        json.loads(my_json)
        speaker = my_json["speaker"]
        message = my_json["prompt"]
        print("主持人:", message)
        if speaker == "結束":
            print("對話結束")
            break
        elif speaker == "美國政府":
            response = chat_session_Am.send_message(message)
            message = response.text
            role_prompt = chat_session.send_message("這是來自美國政府的發言" + message + "請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                    "請你以JSON格式回覆，格式如下\n"\
                                                    "{"\
                                                    "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
                                                    "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                    "}"
                                                    )
            print("美國政府:", message)
        elif speaker == "烏克蘭政府":
            response = chat_session_Uk.send_message(message)
            message = response.text
            role_prompt = chat_session.send_message("這是來自烏克蘭政府的發言" + message + "請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                    "請你以JSON格式回覆，格式如下\n"\
                                                    "{"\
                                                    "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
                                                    "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                    "}"
                                                    )
            print("烏克蘭政府:", message)
        elif speaker == "俄羅斯政府":
            response = chat_session_Ru.send_message(message)
            message = response.text
            role_prompt = chat_session.send_message("這是來自俄羅斯政府的發言" + message + "請你決定誰最適合回答，並且引導他們進行良好的溝通"\
                                                    "請你以JSON格式回覆，格式如下\n"\
                                                    "{"\
                                                    "\"speaker\": \"美國政府/烏克蘭政府/俄羅斯政府/結束\""\
                                                    "\"prompt\": \"引導角色發言並讓整體會談流暢發展\""\
                                                    "}"
                                                    )
            print("俄羅斯政府:", message)
        else:
            print("未知:",speaker)
            sleep(10)
            continue

        sleep(5)

if __name__ == "__main__":
    chat()
