import json
import time
from googletrans import Translator
import google.generativeai as genai
import os
import grpc

# 讀取 JSON 檔案
with open("./json/TASS/cleaned_war in Ukraine_2025_04_20_tass.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 初始化翻譯器
translator = Translator()

# 將標題與內文翻譯成繁體中文
translated_articles = []

# 設定 API 金鑰
api_key = os.environ["GEMINI_API_KEY"] = ""
if not api_key:
    raise ValueError("請設定 GEMINI_API_KEY 環境變數")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

for idx, article in enumerate(data):
    title = article.get("Title", "").strip()
    response2 = model.generate_content(
        title + " 根據以上新聞標題，請幫我翻譯成翻譯中文，盡可能語意通順" +
        "如果沒有標題，請回覆「無標題」" +
        "無需任何其他說明。"
        # generation_config=generation_config
    )
    
    content = article.get("Content", "").strip()
    translated_title = response2.text.strip()
    translated_content = ""

    if not content:
        print(f"[{idx}] 空內容，跳過")
        continue

    success = False
    for attempt in range(2):  # 最多重試三次
        try:
            translated_content = translator.translate(content, src="ru", dest="zh-TW").text
            success = True
            break
        except Exception as e:
            print(f"[{idx}] 翻譯失敗（俄文）第 {attempt + 1} 次：{e}")
            time.sleep(1)

    if not success:
        for attempt in range(2):  # 最多重試兩次
            try:
                translated_content = translator.translate(content, src="en", dest="zh-TW").text
                success = True
                break
            except Exception as e2:
                print(f"[{idx}] 翻譯失敗（英文）第 {attempt + 1} 次：{e2}")
                time.sleep(1)

    if not success:
        print(f"[{idx}] 兩種語言皆翻譯失敗，跳過此筆")

    translated_articles.append({
        "Title": translated_title,
        "URL": article.get("URL", ""),
        "date": article.get("date", ""),
        "TranslatedContent": translated_content
    })

    time.sleep(0.5)  # 避免被限流

# 儲存翻譯後的結果
file_name = "translated_cleaned_Ukraine Russian_2025_04_20.json"
with open("./json/TASS/" + file_name, "w", encoding="utf-8") as file:
    json.dump(translated_articles, file, ensure_ascii=False, indent=4)

print("✅ 翻譯完成，結果已儲存到{}".format(file_name))
