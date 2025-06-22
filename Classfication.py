import google.generativeai as genai
from supabase import create_client, Client
import json
from time import sleep
import os
import jieba  # 使用 jieba 斷詞

# 初始化 Gemini API
api_key = os.getenv("API_KEY_Gemini_PAY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# 初始化 Supabase
api_key_supabase = os.getenv("API_KEY_Supabase")
supabase_url = os.getenv("Supabase_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)

# 從 Supabase 中提取資料
response = (
    supabase.table("generated_news")
    .select("content, date, event_id")
    .execute()
)
data = response.data

# 選擇每個 event_id 最新的一筆資料
latest_news = {}
for item in data:
    event_id = item["event_id"]
    date = item["date"]
    if event_id not in latest_news or date > latest_news[event_id]["date"]:
        latest_news[event_id] = {"content": item["content"], "date": date}

# 類別標籤與說明
label_definitions = """
請你扮演一位資深新聞編輯，針對每一篇新聞進行分類，請從以下 10 個類別中選出所有**有關聯**的類別，可能多於一個。

請以 Python List 格式輸出分類，例如：["Politics", "Technology"]

分類標籤如下：
1. Politics（政治） - 包含政府政策、選舉、外交、政黨動態等。
2. Social News（社會新聞） - 犯罪、公共安全、社會事件、勞工議題等。
3. Science（科學） - 包含科學研究、太空探索、生物科技等。
4. Technology（科技） - 包含 AI、大數據、半導體、電子產品等科技發展。
5. International News（國際） - 重大國際事件、地緣政治、國際組織相關新聞。
6. Lifestyle & Consumer News（生活） - 旅遊、時尚、飲食、消費趨勢等。
7. Sports（運動） - 體育賽事、運動員動態、奧運、世界盃等。
8. Entertainment（娛樂） - 電影、音樂、藝人新聞、流行文化等。
9. Business & Finance（財經） - 經濟政策、股市、企業動態、投資市場等。
10. Health & Wellness（醫療保健） - 公共衛生、醫學研究、醫療技術等。
"""

classified_results = []

# 處理每則新聞
for event_id, news in latest_news.items():
    content = news["content"]
    tokenized_content = list(jieba.cut(content))  # jieba 斷詞

    # 組合提示詞
    prompt = f"""{label_definitions}

新聞原文：
{content}

斷詞結果：
{' / '.join(tokenized_content)}
"""
    # 呼叫 Gemini
    classification = model.generate_content(prompt)
    try:
        classification_list = json.loads(classification.text.strip())  # 嘗試解析為 List
    except Exception as e:
        print(f"[錯誤] event_id {event_id} 回傳無法解析為 JSON List：{classification.text}")
        continue

    # 儲存分類結果
    classified_results.append({
        "event_id": event_id,
        "original_content": content,
        "tokenized_content": tokenized_content,
        "classification_list": classification_list
    })

# 插入分類結果至 Supabase（每個 event_id 可能對應多個分類）
for result in classified_results:
    event_id = result["event_id"]
    for category in result["classification_list"]:
        response = (
            supabase.table("event_category_map")
            .insert({"event_id": event_id, "category": category})
            .execute()
        )
        sleep(0.3)

# 輸出分類結果
for result in classified_results:
    print(f"Event ID: {result['event_id']}")
    print(f"Original Content: {result['original_content']}")
    print(f"Tokenized Content: {result['tokenized_content']}")
    print(f"Classification List: {result['classification_list']}")
    print("-" * 50)
