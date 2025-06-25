import google.generativeai as genai
import json
from time import sleep
import os

# === 2. 設定 Gemini API 金鑰 ===
api_key = ""

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')
#read json
with open('./json/ukrinform/translated_ukrin_to_chinese.json', encoding='utf-8') as f:
    data = json.load(f)

titles = [item['Title'] for item in data]
urls = [item['URL'] for item in data]
contents = [item['TranslatedContent'] for item in data]
dates = [item['date'] for item in data]

print("Titles:", titles)
print("URLs:", urls)
print("Contents:", contents)
print("Dates:", dates)

# Summarize the content

folder = "ukrinform_summary"
os.makedirs(folder, exist_ok=True)

for i in range(len(contents)):
    index=str(i+1)
    summary = model.generate_content("請根據下列新聞文本生成一份摘要，"
                                     "並萃取出主要的關鍵字與事件發生日期。"
                                     "請注意要提取出事件的核心描述、關鍵人物、地點或機構。"
                                     "請以 JSON 格式回傳，格式如下："
                                     "{"
                                     "'Summary': '摘要內容',"
                                     "'Key': ['關鍵字1', '關鍵字2', ...],"
                                     "'Date': 'YYYY-MM-DD'"
                                     "'URL': '新聞網址'"
                                     f"'Index': {index}"
                                     "}"
                                     "新聞文本："
                                     "Title：" + titles[i] + "。"
                                     "URL：" + urls[i] + "。"
                                     "Content：" + contents[i] + "。"
                                     "Date：" + dates[i] + "。"
                                     )      
    print("Summary:", summary.text)
    file_path = os.path.join(folder, f"Summary{i+1}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(summary.text)
    print(f"結果已儲存至 Summary{i+1}.json")
    sleep(60)
