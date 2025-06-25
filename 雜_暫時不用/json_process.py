import json

# key 對應表（你可以加更多）
key_map = {
    "title": "title",
    "url": "url",
    "publishtime": "publish_time",
    "translatedcontent": "translated_content",
    "category": "category",
}

# 你要新增的欄位值
sourceorg_id = 1

def normalize_key(key):
    lower_key = key.lower()
    return key_map.get(lower_key, lower_key)

# 遞迴轉換並新增欄位
def transform_keys(obj):
    if isinstance(obj, dict):
        new_obj = {normalize_key(k): transform_keys(v) for k, v in obj.items()}
        new_obj["sourceorg_id"] = sourceorg_id  # ✅ 新增欄位
        return new_obj
    elif isinstance(obj, list):
        return [transform_keys(item) for item in obj]
    else:
        return obj

# 讀取原始 JSON
with open("your_file.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 轉換資料
converted = transform_keys(data)

# 寫入新檔案
with open("converted_with_sourceorg.json", "w", encoding="utf-8") as f:
    json.dump(converted, f, ensure_ascii=False, indent=2)

print("✅ 已轉換 key 並新增欄位 sourceorg_id")
