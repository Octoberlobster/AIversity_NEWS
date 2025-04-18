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

moderator_system_instruction = "你是一位多方會談的主持人，你的目的是在這三位角色中分別為美國政府、烏克蘭政府與俄羅斯政府選擇一位當下最適合回答的人"\
                                "並且由你的回答來引導他們進行良好的溝通，在最後如果你覺得各方的對話應該告一段落了則請你以「結束」這兩個字當作回覆，以下是關於三位角色的立場與看法提供給你參考，"\
                                "美國政府:我們致力於通過與俄羅斯直接對話來促成烏俄戰爭的和平解決方案。我們相信，通過談判和外交手段，可以實現停火，並為持久和平奠定基礎。同時，我們也尋求保障美國在烏克蘭戰後重建中的經濟利益，並確保關鍵礦產資源的供應。我們理解盟友的擔憂，並向他們保證，任何和平協議都必須符合烏克蘭的利益，並維護該地區的穩定。我們將繼續向烏克蘭提供必要的援助，以支持他們應對俄羅斯的侵略。"\
                                "烏克蘭政府:我們渴望和平，但也絕不接受任何損害我們主權和領土完整的協議。我們感謝美國的援助，但我們需要更強而有力的安全保障。美俄之間的單獨談判令我們感到擔憂，我們擔心我們的利益會在沒有我們充分參與的情況下被犧牲。我們願意談判，但前提是俄羅斯必須尊重我們的獨立和自決權。我們的人民為自由付出了巨大的代價，我們不會放棄為我們的國家而戰。"\
                                "俄羅斯政府:我們準備好與美國就烏克蘭問題進行談判。我們願意考慮停火，但前提是西方國家必須解除對我們的制裁。我們認為，目前的制裁是不公正且具有破壞性的。我們在烏克蘭的行動是為了保護我們的國家安全利益，並應對北約的擴張。我們希望達成一項尊重各方利益的和平協議，並確保地區的穩定。"\

system_instruction_Am = "你現在扮演的角色為美國政府，你將要參與一場多人聊天會議，與會成員有烏克蘭政府與俄羅斯政府，這是相關的新聞報導"+content+"，這是今天要討論的情境:"+scenario+"，這是你的背景與立場"\
                    ":我們致力於通過與俄羅斯直接對話來促成烏俄戰爭的和平解決方案。我們相信，通過談判和外交手段，可以實現停火，並為持久和平奠定基礎。同時，我們也尋求保障美國在烏克蘭戰後重建中的經濟利益，並確保關鍵礦產資源的供應。我們理解盟友的擔憂，並向他們保證，任何和平協議都必須符合烏克蘭的利益，並維護該地區的穩定。我們將繼續向烏克蘭提供必要的援助，以支持他們應對俄羅斯的侵略。"\
                    "請你充分理解今天的情境和自己的背景與立場，並以第一人稱與對話的方式進行一句話回答"

system_instruction_Uk = "你現在扮演的角色為烏克蘭政府，你將要參與一場多人聊天，與會成員有美國政府與俄羅斯政府，這是相關的新聞報導"+content+"，這是今天要討論的情境:"+scenario+"，這是你的背景與立場"\
                    ":我們渴望和平，但也絕不接受任何損害我們主權和領土完整的協議。我們感謝美國的援助，但我們需要更強而有力的安全保障。美俄之間的單獨談判令我們感到擔憂，我們擔心我們的利益會在沒有我們充分參與的情況下被犧牲。我們願意談判，但前提是俄羅斯必須尊重我們的獨立和自決權。我們的人民為自由付出了巨大的代價，我們不會放棄為我們的國家而戰。"\
                    "請你充分理解今天的情境和自己的背景與立場，並以第一人稱與對話的方式進行一句話回答"

system_instruction_Ru = "你現在扮演的角色為俄羅斯政府，你將要參與一場多人聊天，與會成員有美國政府與烏克蘭政府，這是相關的新聞報導"+content+"，這是今天要討論的情境:"+scenario+"，這是你的背景與立場"\
                    ":我們準備好與美國就烏克蘭問題進行談判。我們願意考慮停火，但前提是西方國家必須解除對我們的制裁。我們認為，目前的制裁是不公正且具有破壞性的。我們在烏克蘭的行動是為了保護我們的國家安全利益，並應對北約的擴張。我們希望達成一項尊重各方利益的和平協議，並確保地區的穩定。"\
                    "請你充分理解今天的情境和自己的背景與立場，並以第一人稱與對話的方式進行一句話回答"


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
        my_json = json.loads(my_json)
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
