import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai

input_folder = "json/test"
output_folder = "json/LLM"
os.makedirs(output_folder, exist_ok=True)

api_key = "YOUR_GEMINI_API_KEY"
if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro-002")

all_articles = []
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_articles.extend(data)

news_content = ""
for article in all_articles:
    title = article.get("Title", "")
    url = article.get("URL", "")
    date = article.get("date", "")
    content_raw = article.get("Content", "")
    content = BeautifulSoup(content_raw, "html.parser").get_text().strip()
    news_content += f"標題：{title}\n內容：{content}\n連結：{url}\n日期：{date}\n---\n"

prompt = f"""
你是一位新聞分析專家，以下是一批新聞報導，內容牽涉同一事件但不同日期與來源。請完成以下任務：

1. 請先依照新聞的日期排序，並自行分為 5 個主要階段。
2. 在每個階段中，找出內容相似或重複報導的新聞群組，並將其合併。請為每個階段提煉出一個統整的主題（Topic），字數請勿超過 15 個字。
3. 請列出該階段相關的所有新聞來源（News_sources），若有多家新聞台報導同樣的主題，請合併在同一階段。
4. 最終請回傳一個 JSON 陣列（共 5 個元素），每個元素都必須包含：
   - "Part": 分段編號（1~5）
   - "DateRange": 該階段涵蓋的日期範圍（例如 "2023/01/01 ~ 2023/02/15"）
   - "Topic": 該階段新聞的主題（15 字以內）
   - "News_sources": 此階段相關新聞的來源（list of string）
5. 嚴格遵守 JSON 格式輸出，不要有任何多餘文字或敘述。內容使用繁體中文。

以下是新聞資料：
{news_content}
"""

response = model.generate_content(prompt)
final_text = response.text.replace("```json", "").replace("```", "").strip()

output_file_path = os.path.join(output_folder, "similarity.json")
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"已將相似新聞的 5 段時序分析結果儲存至 {output_file_path}")
