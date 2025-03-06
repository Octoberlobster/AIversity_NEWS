import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
import Summarize

# === 2. 設定 Gemini API 金鑰 ===
api_key = ""

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def CleanNews(news_data):
    cleaned_news = []
    count = 1
    for article in news_data:
        if "content" in article:
            # (1) 去除 HTML
            soup = BeautifulSoup(article["content"], "html.parser")
            cleaned_text = soup.get_text(separator="\n", strip=True)

            # (2) 使用 Gemini API 去除雜訊
            prompt = f"""
            請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

            {cleaned_text}
            """
            response = model.generate_content(prompt)
            article["content"] = response.text.strip()  # 更新文章內容
            print("第", count, "篇文章已清理！")
            cleaned_news.append(article)
            count += 1
    print("🎉 所有文章內容已清理！")
    return Summarize.summarize(cleaned_news)