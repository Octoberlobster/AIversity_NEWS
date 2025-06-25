import json
from googletrans import Translator

# 讀取 JSON 檔案
with open("./json/processed/cleaned_烏俄戰爭_2025_03_30.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 初始化翻譯器
translator = Translator()

# 定義目標語言（西班牙語、英語、中文、日語、韓語、越南語、泰語）
languages = {
    "es": "Spanish",
    "en": "English",
    "zh-TW": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "vi": "Vietnamese",
    "th": "Thai"
}

# 進行翻譯
translated_articles = []

for article in data:
    translated_contents = {}
    for lang_code, lang_name in languages.items():
        translated_contents[lang_name] = translator.translate(article["Content"], src="zh-TW", dest=lang_code).text

    translated_articles.append({
        "Title": article["Title"],
        "URL": article["URL"],
        "date": article["date"],
        "Translations": translated_contents
    })

# 存入 translate.json
with open("translate.json", "w", encoding="utf-8") as file:
    json.dump(translated_articles, file, ensure_ascii=False, indent=4)

print("翻譯完成，結果已儲存到 translate.json。")