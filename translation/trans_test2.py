import json
import time
from googletrans import Translator

# 讀取 JSON 檔案
with open("./json/processed/cleaned_Ukraine Russian_2025_04_16.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 初始化翻譯器
translator = Translator()

# 將標題與內文翻譯成繁體中文
translated_articles = []

for idx, article in enumerate(data):
    title = article.get("Title", "").strip()
    content = article.get("Content", "").strip()
    translated_title = ""
    translated_content = ""

    if not content:
        print(f"[{idx}] 空內容，跳過")
        continue

    success = False
    for attempt in range(3):  # 最多重試三次
        try:
            translated_title = translator.translate(title, src="ru", dest="zh-TW").text
            translated_content = translator.translate(content, src="ru", dest="zh-TW").text
            success = True
            break
        except Exception as e:
            print(f"[{idx}] 翻譯失敗（俄文）第 {attempt + 1} 次：{e}")
            time.sleep(1)

    if not success:
        for attempt in range(3):
            try:
                translated_title = translator.translate(title, src="en", dest="zh-TW").text
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
with open("translated_uke_to_chinese.json", "w", encoding="utf-8") as file:
    json.dump(translated_articles, file, ensure_ascii=False, indent=4)

print("✅ 翻譯完成，結果已儲存到 translated_uke_to_chinese.json。")
