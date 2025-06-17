import json
from supabase import create_client, Client

# 初始化 Supabase 連線
url = ""
key = ""
supabase: Client = create_client(url, key)

# === 🧠 欄位對應 + 預設值 ===
key_map = {
    "title": "title",
    "url": "url",
    "date": "date",
    "content": "content",
}
sourceorg_id = 1  # 你想要塞入的固定值
sourceorg_media = "TASS"  # 你想要塞入的固定值

def normalize_key(key):
    lower_key = key.lower()
    return key_map.get(lower_key, lower_key)

def transform_keys(obj):
    if isinstance(obj, dict):
        new_obj = {normalize_key(k): transform_keys(v) for k, v in obj.items()}

        # 這裡新增 sourceorg_id 欄位

        new_obj["sourcecle_id"] = sourceorg_id + i # ✅ 新增欄位
        new_obj["sourcecle_media"] = sourceorg_media # ✅ 新增欄位

        return new_obj
    elif isinstance(obj, list):
        return [transform_keys(item) for item in obj]
    else:
        return obj

# === 📂 載入 JSON 檔案 ===
with open("./json/ukrinform/cleaned_Ukraine Russian_2025_04_16.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# === 🔁 處理資料 ===
converted_data = transform_keys(data)

# === 🚀 匯入到 Supabase ===
try:
    res = supabase.table("cleaned_news").insert(converted_data).execute()
    print("✅ 匯入成功！", res.data)
except Exception as e:
    print("❌ 匯入失敗：", e)