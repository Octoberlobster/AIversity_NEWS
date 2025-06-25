import google.generativeai as genai
import json
from time import sleep
import glob
import os
import asyncio

# === 1. 設定資料夾路徑 ===
folder_path = "json/TimeLine" # 預測用的
input_folder = "json/progress" # 我的
output_folder = "json/processed"

api_key = "YOUR_GEMINI_API_KEY"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

chat_session = model.start_chat(history=[])
first_message = "接下來我會給你一連串的新聞內容，這些內容都已經依照發生順序給分類好了，也會給你按照時序排好的新聞事件進展，請你記得這些內容，在最後提到\"預測未來\"時請你根據先前的所有新聞與事件進展內容，從三個面向預測未來事件是否會持續發展或停滯(用十五到二十個字之間對每個面向總結除此之外生成關於這篇預測的標題即可)，" \
                "但如果你的預測是會停滯在最後一個事件階段請回答\"事件發展停滯目前階段\""\
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

# === 3. 傳送 Progress 的 DateRange 和 Summary ===
progress_files = glob.glob(os.path.join(input_folder, "*.json"))
progress_messages = []
for pf in progress_files:
    with open(pf, "r", encoding="utf-8") as file:
        data = json.load(file)
        date_range = data.get("DateRange", "")
        summary = data.get("Summary", "")
        if date_range and summary:
            progress_messages.append(f"{date_range}：{summary}")
if progress_messages:
    ans = chat_session.send_message(progress_messages)
    print(ans.text)
    sleep(2)

Predict=chat_session.send_message("預測未來")
with open("Predict.txt", "w", encoding="utf-8") as file:
    file.write(Predict.text)
print(Predict.text)