import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

# === 1. 基本設定 ===
input_folder = "json/test"
output_folder = "json/LLM"
os.makedirs(output_folder, exist_ok=True)
ㄅ
api_key = "YOUR_GEMINI_API_KEY"
if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro-002")

# === 2. 一次讀取所有文章，彙整成一段文字 ===
all_articles = []
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 假設每個 JSON 檔裡面是一個 list 的新聞
            all_articles.extend(data)

#    - 直接把所有新聞的標題、內容、日期、連結都串成一個大字串
news_content = ""
for article in all_articles:
    title = article.get("Title", "")
    content = article.get("Content", "")
    url = article.get("URL", "")
    date = article.get("date", "")
    news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n日期：{date}\n---\n"

prompt = f"""
請閱讀以下多篇新聞，並完成以下任務：

1. 請將所有新聞依時間順序分為 5 個階段，並整理每個時段的事件進展與重要轉折。
2. 為每個時段提供簡要摘要 (Summary)，字數上限 15 字。
3. 將此 5 個階段的結果以 JSON 陣列回覆，陣列中共有 5 個物件，每個物件必須包含以下欄位：
   - "Part": <此時段編號 (1~5)>
   - "DateRange": <此時段所涵蓋的日期範圍，例如 "2023/01/01 ~ 2023/02/15">
   - "Summary": <此時段的 15 字內簡要摘要>
   - "URL": <本時段所有相關新聞連結的陣列>
4. 嚴格遵守 JSON 格式，且不要有 JSON 以外的多餘文字或解釋。
5. 所有內容使用繁體中文。

以下是新聞資料：
{news_content}
"""


response = model.generate_content(prompt)
final_text = response.text.replace("```json", "").replace("```", "").strip()

output_file_path = os.path.join(output_folder, "progress.json")
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"已將結果儲存至 {output_file_path}")
