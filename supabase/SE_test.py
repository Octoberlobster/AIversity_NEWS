import json
from supabase import create_client, Client
import os 
import uuid
import time

# === Supabase 設定 ===
# 初始化 Supabase 連線
url = ""
key = ""
supabase: Client = create_client(url, key)

# === 1. 設定資料夾路徑 ===
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# === 欄位對應 ===
key_map = {
    "title": "title",
    "Title": "title",
    "url": "url",
    "URL": "url",
    "Date": "date",
    "date": "date",
    "content": "content",
    "translatedcontent": "content",
    "Content": "content",
    "Source": "sourcecle_media",
    "source": "sourcecle_media",
    "Image": "image",
}

# sourcecle_media = "ukrinform"  # 來源媒體名稱

def normalize_key(key):
    lower_key = key.lower()
    return key_map.get(lower_key, lower_key)

# 單筆資料處理
def transform_single(obj, index):
    if isinstance(obj, dict):
        new_obj = {normalize_key(k): transform_single(v, index) for k, v in obj.items()}
        new_obj["sourcecle_id"] = index
        return new_obj
    elif isinstance(obj, list):
        return [transform_single(item, index) for item in obj]
    else:
        return obj

# 處理整份資料，加入 index
def transform_all(data, start_index):
    return [transform_single(item, i + start_index + 1) for i, item in enumerate(data[:200])]

def get_current_max_id():
    try:
        res = supabase.table("cleaned_news").select("sourcecle_id").order("sourcecle_id", desc=True).limit(1).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]["sourcecle_id"]
        else:
            return 0
    except Exception as e:
        print("❌ 查詢最大ID失敗：", e)
        return 0
    
# === 載入 JSON ===
# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(output_folder):
    if filename.endswith(".json"):
        output_file_path = os.path.join(output_folder, f"{filename}")
        if(int(get_current_max_id()) <= 200):
            current_max_id = 200
        else:
            current_max_id = int(get_current_max_id())
        # 讀取 JSON 檔案
        with open(output_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        # === 處理轉換 ===
        converted_data = transform_all(raw_data, int(current_max_id))

# === 匯入 Supabase ===
try:
    res = supabase.table("cleaned_news").insert(converted_data).execute()
    print("✅ 匯入成功，共匯入", len(converted_data), "筆")
except Exception as e:
    print("❌ 匯入失敗：", e)
