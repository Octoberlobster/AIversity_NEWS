import google.generativeai as genai
import json
from time import sleep
import glob
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')

folder = "Events"
# 取得所有 JSON 檔案的檔名（假設都在當前目錄）
json_files = glob.glob(os.path.join(folder, "*.json"))
for filename in json_files:
    with open(filename, "r", encoding="utf-8") as f:
        data = f.read()
    print("Data:", data)
    News=model.generate_content("請根據以下多家新聞媒體的新聞內容，統整並生成一篇新的新聞報導，並提供標題與統整內容。請確保內容具有新聞性，並清楚呈現事件的背景、發展與影響。"
                                "輸出格式（請以 JSON 格式回傳）："
                                "{"
                                "\"Title\": \"請生成一個符合新聞風格的標題\","
                                "\"Content\": \"請綜合以下新聞內容，撰寫一篇具邏輯性、流暢且完整的新聞報導\","
                                "\"Date\": \"請填寫新聞生成的日期（格式：YYYY-MM-DD）\""
                                "}"
                                +"需要彙整的新聞內容："
                                +data
                                +"請確保新生成的新聞報導符合以下要求："
                                "1. 維持新聞的公正與專業性"
                                "2. 使用清晰且具邏輯性的語句"
                                "3. 確保內容與事實相符，不加入虛構或未經證實的資訊"
                                "4. 去除重複資訊，統整關鍵觀點，確保內容精煉且具可讀性。"
                                )
    print("News:", News.text)
    file_path = os.path.join("GenerateNews_EachEvent", f"News.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(News.text)
    print(f"結果已儲存至 News.json")
print("所有新聞報導已生成完畢")






