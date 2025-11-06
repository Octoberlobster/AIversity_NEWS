"""從 Supabase 的 single_news 讀取 story_id 與 long，使用 Gemini 生成 2~3 個類別關鍵字並印出。

用法:
  python generate_categories_from_single_news.py [limit]

注意: 請在 Picture_generate_system/.env 設定 SUPABASE_URL、SUPABASE_KEY 與 GEMINI_API_KEY
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
	print("請先在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
	raise SystemExit(1)
if not GEMINI_API_KEY:
	print("請先在 Picture_generate_system/.env 設定 GEMINI_API_KEY")
	raise SystemExit(1)

try:
	from supabase import create_client
except Exception:
	print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
	raise SystemExit(1)

try:
	from google import genai
	from google.genai import types
except Exception:
	print("請先安裝 google genai SDK 並設定 GEMINI_API_KEY")
	raise SystemExit(1)

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else None

client = create_client(SUPABASE_URL, SUPABASE_KEY)

resp = []
batch_size = 1000
start = 0

while True:
    temp = client.table('single_news').select('story_id,long').order("generated_date", desc=True).range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    resp.extend(temp.data)
    start += batch_size

rows = resp or []
if not rows:
	print("未取得資料，請確認表名/權限")
	raise SystemExit(0)

# 初始化 Gemini
genai_client = genai.Client()
MODEL = 'gemini-2.5-flash-lite'  # 使用穩定的模型版本
print(f"使用 Gemini 模型: {MODEL}")

# Step 0: 讀取現有的關鍵字
print("Step 0: 讀取現有的關鍵字...")
existing_resp = []
batch_size = 1000
start = 0

while True:
    temp = client.table('keywords').select('keyword').range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    existing_resp.extend(temp.data)
    start += batch_size
	
if getattr(existing_resp, 'error', None):
	print(f"讀取現有關鍵字失敗: {existing_resp.error}")
	existing_keywords = set()
else:
	existing_data = existing_resp or []
	existing_keywords = {item['keyword'] for item in existing_data if isinstance(item, dict) and item.get('keyword')}
	print(f"已讀取 {len(existing_keywords)} 個現有關鍵字")

# Step 0.5: 讀取已經處理過的 story_id 及其關鍵字數量
print("Step 0.5: 讀取已經處理過的新聞及關鍵字數量...")
processed_resp = []
batch_size = 1000
start = 0

while True:
    temp = client.table('keywords_map').select('story_id, keyword').range(start, start + batch_size - 1).execute()
    if not temp.data:
        break
    processed_resp.extend(temp.data)
    start += batch_size

if getattr(processed_resp, 'error', None):
	print(f"讀取已處理新聞失敗: {processed_resp.error}")
	story_keyword_counts = {}
else:
	processed_data = processed_resp or []
	# 統計每個 story_id 的關鍵字數量
	from collections import defaultdict
	story_keyword_counts = defaultdict(int)
	for item in processed_data:
		if isinstance(item, dict) and item.get('story_id'):
			story_keyword_counts[item['story_id']] += 1
	print(f"已讀取 {len(story_keyword_counts)} 個新聞的關鍵字統計")

def make_prompt(long_text: str, needed_count: int = 3) -> str:
	p = (
		f"請根據下列新聞內容，提出恰好 {needed_count} 個最適合的分類標籤（每個標籤以逗號分隔，且為中文簡短詞，例如：科技、人工智慧、政治、財經、社會，不要超過四個字）。\n"
		f"重要：必須提供恰好 {needed_count} 個標籤，不多不少。\n"
		"只回傳標籤清單，不要額外說明。\n\n"
		f"新聞內容：\n{long_text}\n"
	)
	return p

def extract_keywords_with_retry(genai_client, prompt, model, target_count=3, max_retries=3):
	"""嘗試生成指定數量的關鍵字，如果不符會重試"""
	for attempt in range(max_retries):
		try:
			resp = genai_client.models.generate_content(
				model=model,
				contents=prompt,
				config=types.GenerateContentConfig(response_modalities=['TEXT'], max_output_tokens=60),
			)
			# robust extraction of text from response
			text = None
			# try top-level text
			if hasattr(resp, 'text') and resp.text:
				text = resp.text
			# try candidates
			if text is None:
				cands = getattr(resp, 'candidates', [])
				if cands:
					cand = cands[0]
					# content may be a simple string or object depending on SDK
					cand_content = getattr(cand, 'content', None)
					if isinstance(cand_content, str):
						text = cand_content
					else:
						text = getattr(cand, 'text', None) or getattr(cand, 'content', None)
			out = (text or '').strip().replace('\n', ',')
			# 簡單清理：僅保留中文字、英數、逗號與空白
			import re
			out = re.sub(r"[^\u4e00-\u9fff\w,，\s]", '', out)
			# 將中文逗號統一
			out = out.replace('，', ',')
			# 分割並清理
			labels = [s.strip() for s in out.split(',') if s.strip()]
			
			# 檢查是否有符合目標數量的關鍵字
			if len(labels) == target_count:
				return labels
			elif len(labels) > target_count:
				# 如果超過目標數量，取前 target_count 個
				return labels[:target_count]
			else:
				# 如果少於目標數量，嘗試重新生成
				print(f"第 {attempt + 1} 次嘗試只生成了 {len(labels)} 個關鍵字: {labels}")
				if attempt == max_retries - 1:
					# 最後一次嘗試，補足到目標數量
					while len(labels) < target_count:
						labels.append('其他')
					return labels[:target_count]
		except Exception as e:
			print(f"第 {attempt + 1} 次生成嘗試失敗: {e}")
			if attempt == max_retries - 1:
				return ['其他'] * target_count
	
	return ['其他'] * target_count

# Step 1: 收集所有關鍵字
print("Step 1: 收集所有新聞的關鍵字...")
all_keywords = set()
news_categories = {}  # story_id -> list of keywords

for idx, r in enumerate(rows, start=1):
	if not isinstance(r, dict):
		print(f"Row {idx}: 非典型格式，跳過: {r}")
		continue
	story_id = r.get('story_id') or r.get('id') or f'noid_{idx}'
	
	# 檢查該新聞已有的關鍵字數量
	current_keyword_count = story_keyword_counts.get(story_id, 0)
	
	if current_keyword_count >= 3:
		print(f"跳過已有 {current_keyword_count} 個關鍵字的新聞: {story_id}")
		continue
	elif current_keyword_count > 0:
		needed_keywords = 3 - current_keyword_count
		print(f"新聞 {story_id} 已有 {current_keyword_count} 個關鍵字，需補足 {needed_keywords} 個")
	else:
		needed_keywords = 3
		print(f"新聞 {story_id} 尚無關鍵字，需生成 {needed_keywords} 個")
	
	long = r.get('long') or ''
	if not long:
		print(f"story_id={story_id}：無 long 內容，跳過")
		continue

	prompt = make_prompt(long, needed_keywords)
	
	# 使用新的重試機制確保生成指定數量的關鍵字
	labels = extract_keywords_with_retry(genai_client, prompt, MODEL, needed_keywords)
	
	# 收集關鍵字
	for label in labels:
		all_keywords.add(label)
	news_categories[story_id] = labels
	
	print(f"處理完成 {idx}/{len(rows)}: {story_id} -> {labels}")

# Step 2: 建立去重後的關鍵字列表
print(f"\nStep 2: 去重後的所有關鍵字 ({len(all_keywords)} 個):")
unique_keywords = sorted(list(all_keywords))
for i, keyword in enumerate(unique_keywords):
	print(f"{i+1}. {keyword}")

# Step 2.5: 將去重後的關鍵字存入 keywords 表
new_keywords = [kw for kw in unique_keywords if kw not in existing_keywords]
print(f"\nStep 2.5: 發現 {len(new_keywords)} 個新關鍵字需要存入資料庫...")

if new_keywords:
	insert_count = 0
	fail_count = 0

	for keyword in new_keywords:
		try:
			# 使用 insert（因為已確認是新關鍵字）
			resp = client.table('keywords').insert({'keyword': keyword}).execute()
			if getattr(resp, 'error', None):
				print(f"插入關鍵字 '{keyword}' 失敗: {resp.error}")
				fail_count += 1
			else:
				insert_count += 1
		except Exception as e:
			print(f"插入關鍵字 '{keyword}' 發生例外: {e}")
			fail_count += 1

	print(f"新關鍵字存入完成：成功 {insert_count} 個，失敗 {fail_count} 個")
else:
	print("沒有新關鍵字需要存入資料庫")

# Step 3: 顯示每篇新聞的 categories map
print(f"\nStep 3: 各篇新聞的 categories:")
for story_id, categories in news_categories.items():
	print(f"story_id={story_id}: {categories}")

# Step 4: 將 story_id-keyword 對應關係存入 keywords_map 表
print(f"\nStep 4: 將 story_id-keyword 對應關係存入 keywords_map 表...")
print("注意：如果出現 RLS (Row Level Security) 錯誤，請檢查 Supabase 表權限設定")

# 先讀取現有的 story_id-keyword 組合
existing_pairs = set()
try:
	existing_resp = client.table('keywords_map').select('story_id,keyword').execute()
	if not getattr(existing_resp, 'error', None):
		for item in existing_resp.data or []:
			if isinstance(item, dict) and item.get('story_id') and item.get('keyword'):
				existing_pairs.add((item['story_id'], item['keyword']))
	print(f"已讀取 {len(existing_pairs)} 個現有的 story_id-keyword 組合")
except Exception as e:
	print(f"讀取現有組合失敗: {e}")

map_insert_count = 0
map_fail_count = 0
rls_error_count = 0
duplicate_count = 0

for story_id, categories in news_categories.items():
	for keyword in categories:
		# 檢查是否已存在
		if (story_id, keyword) in existing_pairs:
			duplicate_count += 1
			print(f"跳過已存在組合: {story_id} {keyword}")
			continue
			
		try:
			payload = {
				'story_id': story_id,
				'keyword': keyword
			}
			# 使用普通 insert，因為已經檢查過重複
			resp = client.table('keywords_map').insert(payload).execute()
			if getattr(resp, 'error', None):
				error_msg = str(resp.error)
				if '42501' in error_msg or 'row-level security' in error_msg.lower():
					rls_error_count += 1
					if rls_error_count == 1:  # 只印一次提示
						print(f"RLS 權限錯誤：'{story_id} {keyword}' - 需要在 Supabase 設定 keywords_map 表的插入權限")
				elif '23505' in error_msg or 'duplicate key' in error_msg.lower():
					duplicate_count += 1
					print(f"跳過重複組合: {story_id} {keyword}")
				else:
					print(f"插入對應關係 '{story_id} {keyword}' 失敗: {resp.error}")
				map_fail_count += 1
			else:
				map_insert_count += 1
				print(f"成功插入: {story_id} {keyword}")
				# 加入到已存在集合中
				existing_pairs.add((story_id, keyword))
		except Exception as e:
			error_msg = str(e)
			if '42501' in error_msg or 'row-level security' in error_msg.lower():
				rls_error_count += 1
				if rls_error_count == 1:
					print(f"RLS 權限錯誤：需要在 Supabase Dashboard 設定 keywords_map 表權限")
			elif '23505' in error_msg or 'duplicate key' in error_msg.lower():
				duplicate_count += 1
				print(f"跳過重複組合: {story_id} {keyword}")
			else:
				print(f"插入對應關係 '{story_id} {keyword}' 發生例外: {e}")
			map_fail_count += 1

print(f"對應關係存入完成：成功 {map_insert_count} 筆，失敗 {map_fail_count} 筆，跳過重複 {duplicate_count} 筆")
if rls_error_count > 0:
	print(f"其中 {rls_error_count} 筆因 RLS 權限問題失敗")
	print("解決方法：")
	print("1. 前往 Supabase Dashboard > Authentication > Policies")
	print("2. 為 keywords_map 表新增插入政策，或暫時關閉 RLS")
	print("3. 或改用 service_role key（需小心保管）")

print('完成')

