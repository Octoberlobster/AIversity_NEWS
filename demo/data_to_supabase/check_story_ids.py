#!/usr/bin/env python3
"""檢查 single_news 表中的 story_id 格式"""

from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# 初始化 Supabase 客戶端
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)

# 查看前5筆 story_id
try:
    response = supabase.table('single_news').select('story_id').limit(5).execute()
    
    if response.data:
        print("前5筆 story_id:")
        for i, row in enumerate(response.data, 1):
            story_id = row['story_id']
            print(f"{i}. {story_id}")
    else:
        print("沒有找到任何資料")
        
except Exception as e:
    print(f"查詢失敗: {e}")
