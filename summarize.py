import google.generativeai as genai
import json
from time import sleep
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')

#read json
with open('台灣新聞_cleaned.json', encoding='utf-8') as f:
    data = json.load(f)

titles = [item['Title'] for item in data]
urls = [item['URL'] for item in data]
contents = [item['Content'] for item in data]
dates = [item['Date'] for item in data]

print("Titles:", titles)
print("URLs:", urls)
print("Contents:", contents)
print("Dates:", dates)

# Summarize the content

folder = "summary"

for i in range(len(contents)):
    summary = model.generate_content("請根據下列新聞文本生成一份摘要，"
                                     "並萃取出主要的關鍵字與事件發生日期。"
                                     "請注意要提取出事件的核心描述、關鍵人物、地點或機構。"
                                     "請以 JSON 格式回傳，格式如下："
                                     "{"
                                     "'摘要': '摘要內容',"
                                     "'關鍵字': ['關鍵字1', '關鍵字2', ...],"
                                     "'日期': 'YYYY-MM-DD'"
                                     "}"
                                     "新聞文本："
                                     "標題：" + titles[i] + "。"
                                     "內容：" + contents[i] + "。"
                                     "日期：" + dates[i] + "。"
                                     )      
    print("Summary:", summary.text)
    file_path = os.path.join(folder, f"summary{i}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(summary.text)
    print(f"結果已儲存至 summary{i}.json")
    sleep(60)

