import os
import json
import uuid
import argparse
import time
from dotenv import load_dotenv
from supabase import create_client

print("開始執行腳本...")

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    raise SystemExit(1)
if not GEMINI_API_KEY:
    print("請在 Picture_generate_system/.env 設定 GEMINI_API_KEY")
    raise SystemExit(1)

# 建立 supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Supabase client 建立成功")
except Exception as e:
    print("建立 Supabase client 失敗:", e)
    raise SystemExit(1) from e

# 嘗試匯入 Google GenAI
try:
    import google.genai as genai
    from google.genai import types
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✓ Google Genai 套件已載入")
except ImportError:
    print("請先安裝 google genai SDK：pip install google-genai")
    genai_client = None
    types = None
except Exception as e:
    print(f"Genai client 初始化失敗: {e}")
    genai_client = None
    types = None
    
    
# CLI 參數（預設處理全部；若在執行指令後加數字，則處理該數量）
parser = argparse.ArgumentParser(description="新聞正反方分析（預設處理全部；可於後面加數字指定篇數）")
parser.add_argument("count", nargs="?", type=int, default=None, help="若提供數字，處理該篇數；否則預設處理全部")
parser.add_argument("--limit", type=int, default=None, help="處理上限筆數（與位置參數二擇一，位置參數優先）")
parser.add_argument("--delay", type=float, default=0.6, help="每則新聞呼叫 API 後等待秒數（預設0.6）")
parser.add_argument("--no-save", action="store_true", help="僅產生結果不寫入資料庫")
parser.add_argument("--story-id", type=str, help="指定要處理的 story_id")
args = parser.parse_args()

# 查詢 position_flag 為 true 的新聞
try:
    # 僅查詢 position_flag 為 true 的資料，並取得 story_id, news_title, long 與 category 欄位
    resp = []
    batch_size = 1000
    start = 0
    
    print("開始批次查詢 position 表...")
    while True:
        temp = supabase.table("single_news").select("story_id, news_title, long, category, position_flag").eq("position_flag", True).range(start, start + batch_size - 1).execute()
        if not temp.data:
            break
        resp.extend(temp.data)
        start += batch_size
        print(f"  已查詢 {len(resp)} 筆記錄...")
except Exception as e:
    print("查詢 single_news 時發生錯誤:", e)
    raise SystemExit(1)

if getattr(resp, "error", None):
    print("查詢錯誤:", resp.error)
    raise SystemExit(1)

rows = resp or []
print(f"找到 position_flag 為 true 的新聞筆數: {len(rows)}")

# 查詢已經存在於 position 表中的 story_id（使用批次查詢）
try:
    all_require = []
    batch_size = 1000
    start = 0
    
    print("開始批次查詢 position 表...")
    while True:
        temp = supabase.table("position").select("story_id").range(start, start + batch_size - 1).execute()
        if not temp.data:
            break
        all_require.extend(temp.data)
        start += batch_size
        print(f"  已查詢 {len(all_require)} 筆記錄...")
    
    existing_story_ids = set(row["story_id"] for row in all_require)
    print(f"已在 position 表中的新聞筆數: {len(existing_story_ids)}")
except Exception as e:
    print("查詢 position 表時發生錯誤:", e)
    existing_story_ids = set()

# 過濾掉已經在 position 表中的新聞
rows = [row for row in rows if row.get("story_id") not in existing_story_ids]
print(f"過濾後待處理的新聞筆數: {len(rows)}")

# 根據 --story-id 篩選資料
if args.story_id:
    test_rows = [row for row in rows if row.get("story_id") == args.story_id]
    if not test_rows:
        print(f"❌ 找不到指定的 story_id: {args.story_id}")
        raise SystemExit(1)
    print(f"將處理指定的 story_id: {args.story_id}")
else:
    # 決定要處理的筆數（預設全部；若提供位置參數 count 或 --limit，則以該數為準）
    if args.count is not None:
        test_rows = rows[: args.count]
    elif args.limit is not None:
        test_rows = rows[: args.limit]
    else:
        test_rows = rows[:]  # 預設全部

print(f"執行設定: count={args.count}, limit={args.limit}, delay={args.delay}, no_save={args.no_save}")
print(f"將處理 {len(test_rows)} 筆新聞")

def analyze_pro_con_with_gemini(text: str, news_title: str = None):
    """
    將文章內容送給 Gemini，要求回傳 JSON 格式的正方/反方立場：
    { "pro": ["點1", "點2", ...], "con": ["點1", ...] }
    """
    if genai_client is None:
        print("Gemini client 未初始化，無法呼叫 API。")
        return None

    # 這是您程式碼中應該使用的、修正後的 prompt 字串
    prompt = f"""
你是一位專業的媒體人，擅長以專業且貼近台灣讀者的風格撰寫內容。請根據新聞內容，模擬兩個人針對此議題進行簡單對話辯論。

**對話設定：**
- 正方：支持/贊成此議題的人
- 反方：反對/質疑此議題的人
- 支持觀點與質疑觀點分別陳述，避免直接提到「正方」或「反方」。
- 對話風格：專業、自然，符合台灣讀者的語氣，避免過於艱澀或學術化

請遵守一下內容要求，如果沒做到，你將會遭受極為嚴厲的懲罰。
**內容要求：**
1. 每段對話必須圍繞一個固定的論點展開，避免在同一段對話中跳躍到不同的論點。
2. 每個論點必須引用新聞中的具體細節、數據或事件，不能憑空捏造。
3. 每個論點需包含簡單的邏輯推導，說明為什麼這個觀點是合理的。
4. 從多角度（例如經濟、社會、文化）分析問題，提供更全面的觀點。
5. 使用專業媒體人的語氣，適當加入背景資訊或補充說明，增強內容的深度。
6. 使用台灣讀者熟悉的表達方式。
7. 每個論述限制在150字以內，務必將觀點清楚表達。

**對話流程：**
- 正方針對反方可能的質疑，提出3個具體且有邏輯支撐的反駁
- 反方針對正方可能的支持，提出3個具體且有邏輯支撐的反駁

輸出格式（純JSON，無其他文字）：

{{
  "rebuttals": {{
    "pro_rebuttals": [
      "正方專業反駁一（150字以內，需引用新聞細節並包含邏輯推導）",
      "正方專業反駁二（150字以內，需引用新聞細節並包含邏輯推導）", 
      "正方專業反駁三（150字以內，需引用新聞細節並包含邏輯推導）"
    ],
    "con_rebuttals": [
      "反方專業反駁一（150字以內，需引用新聞細節並包含邏輯推導）",
      "反方專業反駁二（150字以內，需引用新聞細節並包含邏輯推導）",
      "反方專業反駁三（150字以內，需引用新聞細節並包含邏輯推導）"
    ]
  }}
}}

新聞標題：{news_title or ''}
新聞內容：
{text[:2000]}
"""
    try:
        # 使用更新的 genai client 呼叫方式，加入安全設定
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(
                        category='HARM_CATEGORY_HATE_SPEECH',
                        threshold='BLOCK_NONE'
                    ),
                ]
            ) if types else None
        )
        
        # 支援多種回傳欄位取法
        result_text = ""
        if hasattr(response, "text") and isinstance(response.text, str):
            result_text = response.text.strip()
        elif hasattr(response, "output_text") and isinstance(response.output_text, str):
            result_text = response.output_text.strip()
        else:
            try:
                result_text = json.dumps(response.model_dump(), ensure_ascii=False)
            except Exception:
                result_text = str(response)

        # 清理 JSON 格式
        if result_text.startswith('```json'):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith('```'):
            result_text = result_text[3:-3].strip()
        
        # 找出 JSON 片段
        json_start = result_text.find('[')
        json_end = result_text.rfind(']')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            candidate = result_text[json_start:json_end+1]
        else:
            # 如果沒找到陣列，試著找物件
            json_start = result_text.find('{')
            json_end = result_text.rfind('}')
            if json_start != -1 and json_end != -1 and json_end > json_start:
                candidate = result_text[json_start:json_end+1]
            else:
                candidate = result_text

        # 嘗試解析 JSON
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and ("stances" in parsed or "rebuttals" in parsed):
                return parsed
            elif isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # 如果解析失敗，回傳原始文字供檢查
        return {"raw": result_text}
        
    except Exception as e:
        print(f"呼叫 Gemini 失敗: {e}")
        return None

def save_to_database(analysis_result, story_id):
    """
    將分析結果存入 position 資料表
    """
    if analysis_result is None or not isinstance(analysis_result, dict):
        print(f"❌ story_id {story_id}: 沒有有效的分析結果可存入資料庫")
        return False
    
    # 如果結果包含 raw 欄位，嘗試解析其中的 JSON
    if "raw" in analysis_result:
        try:
            raw_content = analysis_result["raw"]
            parsed_raw = json.loads(raw_content)
            analysis_result = parsed_raw
        except json.JSONDecodeError:
            print(f"❌ story_id {story_id}: JSON 解析失敗")
            return False
    
    # 檢查是否有 rebuttals
    if "rebuttals" not in analysis_result:
        print(f"❌ story_id {story_id}: 結果中沒有 rebuttals")
        return False
    
    rebuttals = analysis_result["rebuttals"]
    pro_rebuttals = rebuttals.get("pro_rebuttals", [])
    con_rebuttals = rebuttals.get("con_rebuttals", [])
    
    if not pro_rebuttals and not con_rebuttals:
        print(f"❌ story_id {story_id}: 沒有找到正方或反方的反駁論點")
        return False
    
    try:
        # 生成獨立的 position_id
        position_id = str(uuid.uuid4())
        
        # 準備要存入的資料
        data_to_insert = {
            "position_id": position_id,
            "story_id": story_id,
            "positive": pro_rebuttals,  # 正方反駁存入 positive
            "negative": con_rebuttals   # 反方反駁存入 negative
        }
        
        # 存入資料庫
        response = supabase.table("position").insert(data_to_insert).execute()
        
        if hasattr(response, 'error') and response.error:
            print(f"❌ story_id {story_id}: 存入資料庫失敗 - {response.error}")
            return False
        else:
            print(f"✅ story_id {story_id}: 成功存入資料庫 (position_id: {position_id})")
            return True
            
    except Exception as e:
        print(f"❌ story_id {story_id}: 存入資料庫時發生錯誤 - {e}")
        return False

def pretty_print_analysis(analysis_result, story_id):
    """美化輸出分析結果 - 只顯示 rebuttals"""
    print(f"\n\n==================== 分析 story_id: {story_id} ====================")
    
    if analysis_result is None:
        print("❌ 無回應或呼叫失敗。")
        return
    
    # 如果結果包含 raw 欄位，嘗試解析其中的 JSON
    if isinstance(analysis_result, dict) and "raw" in analysis_result:
        try:
            # 嘗試解析 raw 欄位中的 JSON
            raw_content = analysis_result["raw"]
            parsed_raw = json.loads(raw_content)
            analysis_result = parsed_raw
        except json.JSONDecodeError:
            print("📄 原始輸出：")
            print(analysis_result["raw"])
            return
    
    # 只處理 rebuttals 部分
    if isinstance(analysis_result, dict) and "rebuttals" in analysis_result:
        # 只輸出 rebuttals 的 JSON 格式
        rebuttals_only = {"rebuttals": analysis_result["rebuttals"]}
        print("📄 **分析結果：**")
        print(json.dumps(rebuttals_only, ensure_ascii=False, indent=2))
    else:
        # 如果沒有 rebuttals，顯示完整結果
        print("📄 **分析結果：**")
        print(json.dumps(analysis_result, ensure_ascii=False, indent=2))

# 主流程
if test_rows:
    print(f"\n\n🔍 開始分析 {len(test_rows)} 筆測試新聞...")
    
    successful_saves = 0
    failed_saves = 0
    
    for i, r in enumerate(test_rows, 1):
        sid = r.get("story_id")
        title = r.get("news_title")
        category = r.get("category")
        long_text = r.get("long") or ""
        
        print(f"\n📊 進度: {i}/{len(test_rows)} - 類別: {category}")
        
        # 分析新聞
        result = analyze_pro_con_with_gemini(long_text, news_title=title)
        
        # 顯示分析結果
        pretty_print_analysis(result, sid)
        
        # 存入資料庫（除非 --no-save）
        if not args.no_save:
            if save_to_database(result, sid):
                successful_saves += 1
            else:
                failed_saves += 1
        else:
            print("（dry-run 模式，未寫入資料庫）")
        
        # 等待（避免呼太快）
        time.sleep(args.delay)
    
    print("\n✅ 分析完成！")
    print("📊 統計結果:")
    print(f"   - 共處理: {len(test_rows)} 筆新聞")
    print(f"   - 成功存入: {successful_saves} 筆")
    print(f"   - 存入失敗: {failed_saves} 筆")
else:
    print("❌ 沒有找到符合條件的新聞資料。")