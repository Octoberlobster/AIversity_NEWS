"""檢查每個 story_id 的關鍵字數量

用法:
  python check_keywords_count.py

請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY
"""
import os
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請先在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    raise SystemExit(1)

try:
    from supabase import create_client
except Exception:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    raise SystemExit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)
print(f"連線到 Supabase: {SUPABASE_URL}")

# 讀取所有 keywords_map 資料
print("讀取 keywords_map 表...")
resp = client.table('keywords_map').select('story_id,keyword').execute()
if getattr(resp, 'error', None):
    print(f"讀取 keywords_map 失敗: {resp.error}")
    raise SystemExit(1)

rows = resp.data or []
if not rows:
    print("keywords_map 表為空")
    raise SystemExit(0)

# 統計每個 story_id 的關鍵字
story_keywords = defaultdict(list)
for row in rows:
    if isinstance(row, dict):
        story_id = row.get('story_id')
        keyword = row.get('keyword')
        if story_id and keyword:
            story_keywords[story_id].append(keyword)

print(f"\n找到 {len(story_keywords)} 個新聞 ID 的關鍵字:")
print("=" * 80)

# 統計關鍵字數量分佈
count_distribution = defaultdict(int)
incomplete_stories = []

for story_id, keywords in story_keywords.items():
    keyword_count = len(keywords)
    count_distribution[keyword_count] += 1
    
    if keyword_count != 3:
        incomplete_stories.append((story_id, keyword_count, keywords))
    
    print(f"story_id: {story_id}")
    print(f"關鍵字數量: {keyword_count}")
    print(f"關鍵字: {', '.join(keywords)}")
    print("-" * 40)

# 顯示統計摘要
print("\n關鍵字數量統計:")
print("=" * 30)
for count in sorted(count_distribution.keys()):
    num_stories = count_distribution[count]
    print(f"{count} 個關鍵字: {num_stories} 則新聞")

# 顯示不完整的新聞（非 3 個關鍵字）
if incomplete_stories:
    print(f"\n不完整的新聞 (非 3 個關鍵字): {len(incomplete_stories)} 則")
    print("=" * 50)
    for story_id, count, keywords in incomplete_stories:
        print(f"{story_id}: {count} 個關鍵字 -> {', '.join(keywords)}")
else:
    print(f"\n✓ 所有新聞都有恰好 3 個關鍵字")

print(f"\n總計: {len(story_keywords)} 則新聞，{sum(len(kws) for kws in story_keywords.values())} 個關鍵字對應關係")
