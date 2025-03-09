import json
import os
import glob
import Categorize

folder = "Summary"
# 取得所有 JSON 檔案的檔名（假設都在當前目錄）
json_files = glob.glob(os.path.join(folder, "*.json"))

def combined(summary_list):
    
    combined_data = []

    for i in range(len(summary_list)):
        combined_data.append(summary_list[i])


    # 將合併後的資料寫入一個新的 JSON 檔案
    with open("Combined.json", "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)

    print("合併完成，所有 JSON 檔案已合併成 Combined.json")
    
    return Categorize.category(combined_data)