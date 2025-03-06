import json
import os
import GenerateNews

# 讀取原始 JSON 檔案
input_file = "Categorize.json"  # 請替換為你的 JSON 檔名
output_folder = "Events"  # 儲存分割後 JSON 的資料夾

def divide(data):
    
    data = data.replace('```json', '').replace('```', '').strip()
    
    data = json.loads(data)
    print("Data:", data)
    event_list = []
    
    # 遍歷 JSON 中的每個事件名稱，並存成獨立的 JSON 檔案
    for event_name, event_data in data.items():
        # 生成合法的檔案名稱（移除特殊字元）
        safe_event_name = "_".join(event_name.split())
        output_path = os.path.join(output_folder, f"{safe_event_name}.json")
        
        # 儲存 JSON
        with open(output_path, "w", encoding="utf-8") as out_file:
            json.dump({event_name: event_data}, out_file, ensure_ascii=False, indent=4)
        
        single_event = {event_name: event_data}
        print(f"已儲存: {output_path}")
        event_list.append(single_event)
    print("分割完成，所有事件已儲存至 Events 資料夾")
    print(event_list)
    
    return GenerateNews.generate(event_list)