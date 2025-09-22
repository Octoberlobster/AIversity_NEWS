import json
from supabase import create_client, Client
import os

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")  # 替換為您的 Supabase URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # 替換為您的 Supabase Anon Key

# 初始化 Supabase 客戶端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_json_to_topic(topic_id: str, json_data: dict):
    """
    上傳 JSON 資料到指定 topic 的 mind_map_detail 欄位
    
    Args:
        topic_id (str): Topic ID
        json_data (dict): 要上傳的 JSON 資料
    
    Returns:
        dict: 更新結果
    """
    try:
        # 更新指定 topic 的 mind_map_detail 欄位
        result = supabase.table('topic').update({
            'mind_map_detail': json_data
        }).eq('topic_id', topic_id).execute()
        
        if result.data:
            print(f"✅ 成功更新 topic {topic_id}")
            return result.data
        else:
            print(f"❌ 找不到 topic {topic_id}")
            return None
            
    except Exception as e:
        print(f"❌ 上傳失敗: {str(e)}")
        return None

def upload_json_from_file(topic_id: str, json_file_path: str):
    """
    從 JSON 檔案讀取資料並上傳
    Args:
        topic_id (str): Topic ID
        json_file_path (str): JSON 檔案路徑
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        return upload_json_to_topic(topic_id, json_data)
        
    except FileNotFoundError:
        print(f"❌ 找不到檔案: {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"❌ JSON 格式錯誤: {json_file_path}")
        return None

# 主要執行程式
if __name__ == "__main__":
    # 您指定的 topic_id
    TOPIC_ID = "49cbf695-7d16-4558-aaa3-79b8a17997f5"
    
    # 方法 2: 從檔案上傳 (如果您有 JSON 檔案)
    json_file_path = "json/5W1H/大罷免_5W1H_20250831_202817.json"  # 替換為您的 JSON 檔案路徑
    
    print("方法 2: 從檔案上傳")
    print(f"嘗試從 {json_file_path} 讀取資料...")
    
    # 如果檔案存在則上傳
    import os
    if os.path.exists(json_file_path):
        result = upload_json_from_file(TOPIC_ID, json_file_path)
        print(f"結果: {result}")
    else:
        print(f"檔案 {json_file_path} 不存在，跳過方法 2")

    print("\n程式執行完畢！")