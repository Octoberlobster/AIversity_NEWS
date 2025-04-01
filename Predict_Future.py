import google.generativeai as genai
import json
from time import sleep
import glob
import os
import asyncio

# 設定 API 金鑰
api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
folder_path = "TimeLine"

model = genai.GenerativeModel('gemini-1.5-pro-002')

chat_session = model.start_chat(history=[])
first_message = "接下來我會給你一連串的新聞內容，這些內容都已經依照發生順序給分類好了，請你記得這些內容，在最後提到\"預測未來\"時請你幫我根據先前的內容以三種面向來預測近日可能發生的未來(用十五到二十個字之間對每個面向總結即可)，" \
                "如果你有接收到我的指示，請一律回答\"是的\"，謝謝！"
ans=chat_session.send_message(first_message)
print(ans.text)
sleep(10)
# 取得所有 JSON 檔案的檔名（假設都在當前目錄）
json_files = glob.glob(os.path.join(folder_path, "*.json"))#目前沒問題但如果檔名有11或12的月份會有問題
for f in json_files:
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
        content = json.loads(content)
        for key in content.keys():  # 取得 JSON 的頂層 key（可能變動）
            if "進展" in content[key]:  # 確保這個 key 內有 "進展"
                summaries = [item["摘要"] for item in content[key]["進展"]]
        ans=chat_session.send_message(summaries)
        print(ans.text)
        sleep(2)
Predict=chat_session.send_message("預測未來")
with open("Predict.txt", "w", encoding="utf-8") as file:
    file.write(Predict.text)
print(Predict.text)




