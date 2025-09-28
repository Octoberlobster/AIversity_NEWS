# pip install requests
from env import supabase, translate_api_key
import requests

API_URL = "https://translation.googleapis.com/language/translate/v2"

# 1) 從 Supabase 抓前 5 筆
rows = supabase.table("single_news").select("story_id, ultra_short").limit(5).execute().data
payload = [ (r["story_id"], (r.get("ultra_short") or "").strip()) for r in rows ]
texts = [t for _, t in payload if t]

if not texts:
    print("沒有可翻譯的內容")
else:
    # 2) 呼叫 v2 REST（使用 API key）
    params = {"key": translate_api_key}
    data = {
        "q": texts,                 # 可一次傳 list
        "target": "fr",             # 目標語言
        "format": "text"            # 或 "html"
        # "source": "zh-TW"         # 想固定來源語言可加上
    }
    resp = requests.post(API_URL, params=params, json=data, timeout=30)
    resp.raise_for_status()
    translations = resp.json()["data"]["translations"]  # 與 texts 對應

    it = iter(translations)
    for rid, txt in payload:
        if not txt:
            print(f"[{rid}] (空白)")
            continue
        t = next(it)
        print(t)
        print("-" * 40)
        print(f"[{rid}]")
        print("原文:", txt)
        print("偵測語言:", t.get("detectedSourceLanguage"))
        print("翻譯:", t["translatedText"])   # 可能含 HTML 實體
        print("-" * 40)
