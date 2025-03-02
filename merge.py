import json
import os
import glob

folder = "summary"
# 取得所有 JSON 檔案的檔名（假設都在當前目錄）
json_files = glob.glob(os.path.join(folder, "*.json"))

combined_data = []

# 讀取每個 JSON 檔案並將資料加入 combined_data
for filename in json_files:
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace('```json', '').replace('```', '').strip()
    data = json.loads(content)
    combined_data.append(data)

# 將合併後的資料寫入一個新的 JSON 檔案
with open("combined.json", "w", encoding="utf-8") as f:
    json.dump(combined_data, f, ensure_ascii=False, indent=4)

print("合併完成，所有 JSON 檔案已合併成 combined.json")
