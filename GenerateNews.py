import google.generativeai as genai
import json
from time import sleep
import glob
import os

api_key = os.getenv("API_KEY_Gemini2")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')

folder = "Events"
# 取得所有 JSON 檔案的檔名（假設都在當前目錄）
json_files = glob.glob(os.path.join(folder, "*.json"))
index = 1
for filename in json_files:
    with open(filename, "r", encoding="utf-8") as f:
        data = f.read()
    print("Data:", data)
    News=model.generate_content("請根據以下彙整的新聞內容，生成一篇新的新聞報導，並提供標題與統整內容。請確保內容具有新聞性，並清楚呈現事件的背景、發展與影響。"
                                "輸出格式（請以 JSON 格式回傳）："
                                "{"
                                "'Title': '請生成一個符合新聞風格的標題',"
                                "'Content': '請綜合以下新聞內容，撰寫一篇具邏輯性、流暢且完整的新聞報導',"
                                "'References': '請列出引用的原始新聞索引（以逗號分隔，例如：1,2,3,4）',"
                                "'Category': '不需要填，留白即可',"
                                "'Date': '請填寫新聞生成的日期（格式：YYYY-MM-DD）',"
                                f"'Index': {index}"
                                "}"
                                +"需要彙整的新聞內容："
                                +data
                                +"請確保新生成的新聞報導符合以下要求："
                                "維持新聞的公正與專業性"
                                "使用清晰且具邏輯性的語句"
                                "確保內容與事實相符，不加入虛構或未經證實的資訊"
                                )
    print("News:", News.text)
    file_path = os.path.join("GenerateNews_EachEvent", f"News{index}.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(News.text)
    print(f"結果已儲存至 News{index}.json")
    index += 1
    sleep(60)
print("所有新聞報導已生成完畢")






