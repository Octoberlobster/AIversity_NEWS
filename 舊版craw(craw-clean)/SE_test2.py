import json
from supabase import create_client, Client
import os 
import uuid
import time
import shutil

# === Supabase 設定 ===
# 初始化 Supabase 連線
SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# === 1. 設定資料夾路徑 ===
output_folder = "json"
move_folder = "json"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)
os.makedirs(move_folder, exist_ok=True)  # ✅ 確保移動資料夾存在

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
def transform_single(obj):
    if isinstance(obj, dict):
        new_obj = {normalize_key(k): transform_single(v) for k, v in obj.items()}
        new_obj["sourcecle_id"] = generate_uuid(obj.get("sourcecle_id", ""))
        return new_obj
    elif isinstance(obj, list):
        return [transform_single(item) for item in obj]
    else:
        return obj

def transform_all(data):
    return [transform_single(item) for item in data[:200]]

def generate_uuid(val):
    try:
        # 若是合法 UUID 字串，轉成 UUID 沒問題
        return str(uuid.UUID(val))
    except:
        # 若不是，就新產一個 UUID
        return str(uuid.uuid4())
    
# === 載入 JSON ===
# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(output_folder):
    if filename.endswith(".json"):
        output_file_path = os.path.join(output_folder, f"{filename}")

        # 讀取 JSON 檔案
        with open(output_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # === 處理轉換 ===
        converted_data = transform_all(raw_data)

        # === 匯入 Supabase ===
        try:
            res = supabase.table("cleaned_news").insert(converted_data).execute()
            print("✅ 匯入成功，共匯入", len(converted_data), "筆")

            # ✅ 將原始檔案移動到 move_folder
            shutil.move(output_file_path, os.path.join(move_folder, filename))
            print(f"✅ {filename} 處理完成！已儲存至 {output_file_path} 並移動原始檔案。")
        except Exception as e:
            print("❌ 匯入失敗：", e)
