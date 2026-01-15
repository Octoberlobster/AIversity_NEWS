import os, json, re
from supabase import create_client
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional
import random, hashlib
from pathlib import Path
from datetime import datetime

# ========================================
# 系統初始化與資料獲取
# ========================================

def initialize_services():
    """初始化 Supabase 和 Gemini 服務連接"""
    load_dotenv()
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return supabase, gemini

def fetch_data_from_database(supabase):
    """從資料庫獲取專題和新聞資料"""
    topic = supabase.table("topic").select("topic_id, topic_title").eq("alive", 1).execute()
    print(topic.data)
    
    news = []
    batch_size = 1000
    start = 0
    while True:
        temp = supabase.table("single_news").select("story_id, news_title, short").order("generated_date", desc=True).range(start, start + batch_size - 1).execute()
        if not temp.data:
            break
        news.extend(temp.data)
        break
        start += batch_size
    return topic, news

def get_classified_news_ids(supabase) -> set[str]:
    """獲取已經分類的新聞 ID 集合"""
    try:
        result = supabase.table("topic_news_map").select("story_id").execute()
        if result.data:
            classified_story_ids = {str(item["story_id"]) for item in result.data}
            print(f"找到 {len(classified_story_ids)} 個已分類的新聞")
            return classified_story_ids
        else:
            print("沒有找到已分類的新聞")
            return set()
    except Exception as e:
        print(f"獲取已分類新聞失敗: {e}")
        return set()

def filter_new_news_only(news_data, classified_story_ids: set[str]) -> list[dict]:
    """過濾出只有未分類的新聞"""
    new_news = []
    already_classified = []
    
    for item in news_data:
        story_id = str(item["story_id"])
        news_title = item.get("news_title", "")
        
        if story_id in classified_story_ids:
            already_classified.append({"story_id": story_id, "news_title": news_title})
        else:
            new_news.append(item)
    
    print(f"\n📰 新聞分析統計:")
    print(f"   未分類新聞: {len(new_news)} 篇")
    print(f"   已分類新聞: {len(already_classified)} 篇")
    print(f"   總新聞數: {len(news_data)} 篇")
    
    if not new_news:
        print("\n⚠️  所有新聞都已分類，無需處理")
        return []
    
    return new_news

# ========================================
# 資料模型
# ========================================

class TopicBrief(BaseModel):
    short_description: str = Field(max_length=120)
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list, description="代表此專題的5-8個核心關鍵詞")
    positive_examples: list[str] = Field(default_factory=list, description="1-2個最能代表此專題的『新聞標題』範例")
    negative_examples: list[str] = Field(default_factory=list, description="1-2個容易混淆但『不屬於』此專題的『新聞標題』範例")

class LMLabel(BaseModel):
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None

# ========================================
# AI 提示詞建構
# ========================================
def build_topic_description_prompt(topic_title: str) -> str:
    """建構專題描述生成的 AI 提示詞"""
    return f"""專題標題：{topic_title}

任務：請為這個專題生成一份詳細的 JSON 格式檔案，以利後續的AI模型能精準地將新聞歸類到此專題。

規則：
- 允許上網檢索近 3–5 年公開資料以釐清定義與常見範圍。
- **只輸出 JSON**，不得有任何其他文字。JSON 欄位與說明如下：
  - short_description (字串): 控制在 100–110 字（最多 120 字），1–2 句，說明本專題的主題邊界與常見範圍。
  - aliases (字串陣列): 常見別名或縮寫。
  - keywords (字串陣列): 提供 5-8 個最能代表此專題的核心關鍵詞。
  - positive_examples (字串陣列): 提供 1-2 個「絕對屬於」此專題的『模擬新聞標題』範例。
  - negative_examples (字串陣列): 提供 1-2 個「容易混淆，但**不屬於**」此專題的『模擬新聞標題』範例，以幫助 AI 釐清邊界。
- 避免寫入單一事件或單一公司名稱，除非該名稱已成為主題的代名詞。
- 若初稿超長，請自行刪減至符合字數限制；所有欄位不得為空值，若無內容則回傳空陣列 `[]`。
"""

def build_classification_prompt(story_title: str, story_short: str, topics_payload: list[dict]) -> str:
    """建構新聞分類的 AI 提示詞"""
    NEWS_MAX_CHARS = 1200
    
    article = (story_title or "").strip()
    if story_short:
        article += "\n\n" + (story_short or "").strip()
    article = article[:NEWS_MAX_CHARS]

    topics_json = json.dumps(topics_payload, ensure_ascii=False)

    return (
        "任務：根據下方提供的『候選專題清單』與『本文』，請在候選清單中選出最合適的一個專題；若全部不合適，請回 null。\n"
        "輸出：僅輸出 JSON，且**必須完全符合**此結構（不可有多餘欄位或文字）：\n"
        '{\"topic_id\": <UUID或null>, \"topic_title\": <字串或null>}\n\n'
        "規則：\n"
        "1) **請仔細評估每個專題的描述(desc)、關鍵詞(keywords)與分類指導(guidelines)。**\n"
        "2) **`guidelines` 中的 `includes_examples` 是正面範例，`excludes_examples` 是反面範例，這對於釐清專題邊界至關重要。**\n"
        "3) 只能從候選清單中選；不可發明清單外的標籤。\n"
        "4) 若皆不合適：topic_id = null、topic_title = null。\n"
        "5) topic_title 請對應所選 topic_id 的 title。\n\n"
        f"【候選專題清單（JSON 陣列）】\n{topics_json}\n\n"
        f"【本文】\n標題：{story_title}\n內容摘錄：\n{article}\n"
    )

# ========================================
# 文字處理工具函數
# ========================================
def clamp_description(s: str, min_len: int = 100, max_len: int = 110, hard_max: int = 120) -> str:
    """限制描述長度並優化截斷位置"""
    s = re.sub(r"\s+", " ", (s or "").strip())
    if len(s) <= max_len:
        return s
    cut = s[:max_len]
    punct = "，,、;；。.!?？)]」』】）"
    tail = cut[-15:]
    idx = max(tail.rfind(ch) for ch in punct)
    if idx >= 0 and (len(cut) - (15 - idx)) >= min_len:
        cut = cut[: len(cut) - (15 - idx)]
    out = cut.rstrip()
    if len(s) > len(out):
        out += "…"
    return out[:hard_max]

def extract_json_candidate(text: str) -> Optional[str]:
    """從文字中提取 JSON 候選字串"""
    if not text:
        return None
    s = text.strip()

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, flags=re.S)
    if fence:
        return fence.group(1)

    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()

    try:
        json.loads(s)
        return s
    except Exception:
        pass

    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(s[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = s[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    continue
    return None

# ========================================
# AI 回應處理與專題描述生成
# ========================================
def repair_response_to_json(gemini_client, bad_text: str) -> TopicBrief:
    """修復格式錯誤的回應為合法 JSON"""
    resp2 = gemini_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=f"請將下列內容只轉為合法 JSON（欄位：short_description, aliases）。不得加入任何多餘文字：\n{bad_text}",
        config=types.GenerateContentConfig(
            system_instruction="你是格式化工具，只輸出合法 JSON。",
            response_mime_type="application/json",
            response_schema=TopicBrief,
            temperature=0,
        ),
    )
    fixed: TopicBrief = resp2.parsed
    fixed.short_description = clamp_description(fixed.short_description, 100, 110, 120)
    return fixed

def safe_label_from_response(resp) -> LMLabel:
    """安全地從 AI 回應中解析標籤，確保永遠回傳 LMLabel"""
    # 預設
    label = LMLabel(topic_id=None, topic_title=None)

    # 1) 先試 parsed
    parsed = getattr(resp, "parsed", None)
    if parsed is not None:
        if isinstance(parsed, LMLabel):
            return parsed
        try:
            return LMLabel.model_validate(parsed)
        except Exception:
            pass

    # 2) 退回 text -> JSON
    txt = (getattr(resp, "text", "") or "").strip()
    if txt:
        cand = extract_json_candidate(txt) or txt
        try:
            data = json.loads(cand)
            return LMLabel.model_validate(data)
        except Exception:
            pass

    # 3) 全失敗 → 預設
    return label

# ========= 專題描述生成函數 =========
def generate_topic_description(gemini_client, topic_title: str) -> TopicBrief:
    """為單個專題生成 AI 描述"""
    # 第一次：開工具（允許上網），但不鎖 JSON MIME
    resp = gemini_client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=build_topic_description_prompt(topic_title),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            system_instruction="你是新聞專題描述助理。輸出繁體中文、客觀、精簡，供前端 tooltip 使用。",
            temperature=0.2,
        )
    )

    brief: Optional[TopicBrief] = None
    raw = (resp.text or "").strip()

    cand = extract_json_candidate(raw)
    if cand:
        try:
            data = json.loads(cand)
            desc = clamp_description(data.get("short_description", ""), 100, 110, 120)
            aliases = data.get("aliases", []) or []
            brief = TopicBrief(short_description=desc, aliases=aliases)
        except Exception:
            brief = None

    if brief is None:
        try:
            brief = repair_response_to_json(gemini_client, raw if raw else f'{{"short_description": "本專題：{topic_title}", "aliases": []}}')
        except Exception:
            brief = None

    if brief is None:
        fallback = f"本專題聚焦「{topic_title}」，彙整近年相關政策、事件、產業與社會影響，提供脈絡要點與趨勢觀察，協助讀者快速掌握重點與延伸討論。"
        brief = TopicBrief(short_description=clamp_description(fallback, 100, 110, 120), aliases=[])

    return brief

def build_topic_profiles(gemini_client, topics_to_process) -> dict[str, dict]:
    """建立專題的 AI 描述檔案"""
    topic_profiles: dict[str, dict] = {}
    
    if not topics_to_process:
        print("沒有需要處理的專題，跳過建立描述檔案")
        return topic_profiles
    
    print(f"開始為 {len(topics_to_process)} 個專題建立描述檔案...")
    
    for item in topics_to_process:
        topic_title = item["topic_title"]
        brief = generate_topic_description(gemini_client, topic_title)
        
        print(f"[{topic_title}] {brief.short_description} (len={len(brief.short_description)}) | aliases={brief.aliases}")
        
        tid = str(item["topic_id"])
        topic_profiles[tid] = {
            "title": topic_title,
            "desc": brief.short_description,
            "aliases": brief.aliases,
            "keywords": brief.keywords,
            "positive_examples": brief.positive_examples,
            "negative_examples": brief.negative_examples,
        }
    
    return topic_profiles

# ========================================
# 專題資料準備
# ========================================
def build_topics_payload(topic_profiles: dict[str, dict], max_aliases: int = 6) -> list[dict]:
    """建立專題候選清單"""
    items = []
    for tid, prof in topic_profiles.items():
        aliases = [a.strip() for a in (prof.get("aliases") or []) if a and a.strip()]
        aliases = aliases[:max_aliases]

        guidelines = {
            "includes_examples": prof.get("positive_examples", []),
            "excludes_examples": prof.get("negative_examples", [])
        }

        items.append({
            "topic_id": tid,
            "title": prof.get("title", ""),
            "desc": prof.get("desc", ""),
            "aliases": aliases,
            "keywords": prof.get("keywords", []),
            "guidelines": guidelines,
        })
    return items

def shuffle_topics_for_story(topics_payload: list[dict], story_id: str) -> list[dict]:
    """為特定新聞產生可重現的隨機順序專題列表"""
    seed = int(hashlib.md5(story_id.encode("utf-8")).hexdigest(), 16) % (10**8)
    rnd = random.Random(seed)
    copied = topics_payload[:]
    rnd.shuffle(copied)
    return copied

# ========================================
# 新聞分類處理
# ========================================
def classify_single_news(gemini_client, story_id: str, story_title: str, story_short: str, topics_payload: list[dict], topic_profiles: dict) -> dict:
    """分類單則新聞"""
    SKIP_NONE = False
    
    if not (story_title or story_short):
        if not SKIP_NONE:
            return {
                "topic_id": None,
                "topic_title": None,
                "source_story": {"story_id": story_id, "news_title": story_title, "short": story_short},
            }
        print(f"[story_id={story_id}]（空文本） → topic_id=NONE")
        return None

    candidates = shuffle_topics_for_story(topics_payload, story_id)
    prompt = build_classification_prompt(story_title, story_short, candidates)

    # 不開工具，才能安全使用 JSON schema
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="你是新聞歸類助理。僅依照指示輸出 JSON（topic_id, topic_title）。",
                response_mime_type="application/json",
                response_schema=LMLabel,
                temperature=0.1,
            )
        )
        label = safe_label_from_response(resp)
    except Exception as e:
        label = LMLabel(topic_id=None, topic_title=None)
        print(f"[story_id={story_id}] LLM 呼叫失敗：{e} → topic_id=NONE")

    # 以 topic_id 為準，避免模型把 title 打錯；用你的 canonical title 覆寫
    tid = label.topic_id if (label.topic_id and label.topic_id in topic_profiles) else None
    ttitle = topic_profiles[tid]["title"] if tid else None

    result_obj = {
        "topic_id": tid,
        "topic_title": ttitle,
        "source_story": {
            "story_id": story_id,
            "news_title": story_title,
            "short": story_short,
        }
    }

    shown = tid if tid else "NONE"
    print(f"[story_id={story_id}] {story_title}\n  → topic_id={shown}")
    
    return result_obj

def classify_all_news(gemini_client, news_data, topics_payload: list[dict], topic_profiles: dict) -> list[dict]:
    """分類所有新聞"""
    classified_results: list[dict] = []
    SKIP_NONE = False

    for doc in news_data.data:
        sid = str(doc["story_id"])
        s_title = (doc.get("news_title") or "").strip()
        s_short = (doc.get("short") or "").strip()
        
        result = classify_single_news(gemini_client, sid, s_title, s_short, topics_payload, topic_profiles)
        
        if result is not None:
            if not ((result.get("topic_id") is None) and SKIP_NONE):
                classified_results.append(result)

    return classified_results

# ========================================
# 資料庫操作
# ========================================
def append_topic_news_mappings(supabase, topic_id: str, story_ids: list[str]) -> bool:
    """將新的專題和新聞映射關係追加到資料庫（增量模式）"""
    try:
        # 先檢查哪些 story_id 已經存在
        existing_result = supabase.table("topic_news_map").select("story_id").eq("topic_id", topic_id).execute()
        existing_story_ids = {str(item["story_id"]) for item in existing_result.data} if existing_result.data else set()
        
        # 過濾出真正需要新增的 story_id
        new_story_ids = [sid for sid in story_ids if sid not in existing_story_ids]
        
        if not new_story_ids:
            print(f"專題 {topic_id} 沒有需要新增的新聞映射")
            return True
        
        # 準備要插入的資料
        mappings = [
            {
                "topic_id": topic_id,
                "story_id": story_id
            }
            for story_id in new_story_ids
        ]
        
        # 批量插入
        result = supabase.table("topic_news_map").insert(mappings).execute()
        
        if result.data:
            print(f"成功為專題 {topic_id} 新增 {len(new_story_ids)} 筆新聞映射")
            return True
        else:
            print(f"為專題 {topic_id} 新增映射失敗：無資料返回")
            return False
            
    except Exception as e:
        print(f"為專題 {topic_id} 新增映射失敗: {e}")
        return False

def save_incremental_results_to_database(supabase, grouped_output: dict) -> dict:
    """將分類結果增量存入資料庫（不清除現有資料，只新增）"""
    saved_topics = []
    failed_topics = []
    
    print(f"\n開始增量存入資料庫...")
    
    for topic in grouped_output["topics"]:
        topic_id = topic["topic_id"]
        topic_title = topic["topic_title"]
        stories = topic["stories"]
        news_count = len(stories)
        
        # 如果這個專題沒有新新聞，跳過
        if news_count == 0:
            continue
        
        # 準備新聞 ID 列表
        story_ids = [story["story_id"] for story in stories]
        
        # 增量插入新的映射（不清除現有的）
        if append_topic_news_mappings(supabase, topic_id, story_ids):
            saved_topics.append({
                "topic_id": topic_id,
                "topic_title": topic_title,
                "new_news_count": news_count
            })
            print(f"✅ 成功為專題 '{topic_title}' 新增: {news_count} 篇新聞")
        else:
            failed_topics.append({
                "topic_id": topic_id,
                "topic_title": topic_title,
                "new_news_count": news_count,
                "reason": "新增映射失敗"
            })
            print(f"❌ 為專題 '{topic_title}' 新增新聞失敗")
    
    # 統計結果
    summary = {
        "saved_count": len(saved_topics),
        "failed_count": len(failed_topics),
        "total_topics": len(grouped_output["topics"]),
        "saved_topics": saved_topics,
        "failed_topics": failed_topics,
        "mode": "incremental"
    }
    
    print(f"\n📊 增量資料庫存入摘要:")
    print(f"   成功新增: {summary['saved_count']} 個專題的新聞")
    print(f"   失敗: {summary['failed_count']} 個專題")
    print(f"   處理的專題數: {summary['total_topics']} 個專題")
    
    return summary

# ========================================
# 結果處理與檔案輸出
# ========================================
def group_results_by_topic(classified_results: list[dict], topic_profiles: dict) -> dict:
    """依專題分組結果"""
    groups_map: dict[str, dict] = {
        tid: {"topic_id": tid, "topic_title": prof["title"], "stories": []}
        for tid, prof in topic_profiles.items()
    }
    unassigned: list[dict] = []

    for rec in classified_results:
        tid = rec["topic_id"]
        story = rec["source_story"]
        if tid is None:
            unassigned.append(story)
        else:
            bucket = groups_map.setdefault(
                tid,
                {"topic_id": tid, "topic_title": rec.get("topic_title") or topic_profiles.get(tid, {}).get("title"), "stories": []}
            )
            bucket["stories"].append(story)

    grouped_output = {
        "topics": list(groups_map.values()),
        "unassigned": unassigned
    }
    
    return grouped_output

def save_results_to_file(grouped_output: dict) -> Path:
    """儲存結果到檔案"""
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"classified_grouped_{datetime.now():%Y%m%d_%H%M%S}.json"
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(grouped_output, f, ensure_ascii=False, indent=2)
    
    return out_path

def print_summary(grouped_output: dict, out_path: Path):
    """印出處理摘要"""
    topics_with_stories = sum(1 for g in grouped_output["topics"] if g["stories"])
    print(f"\n✅ 已輸出分組結果：共 {len(grouped_output['topics'])} 個主題（其中 {topics_with_stories} 個有分到文章），未分類 {len(grouped_output['unassigned'])} 則 → {out_path}")

# ========================================
# 主流程
# ========================================
def main():
    """主流程：拉取所有專題，只分類未分類的新聞"""
    print("🚀 啟動新聞分類系統")
    
    # 初始化服務
    supabase, gemini = initialize_services()
    
    # 獲取資料
    topic_data, news_data = fetch_data_from_database(supabase)
    
    # 找出已分類的新聞
    classified_story_ids = get_classified_news_ids(supabase)
    
    # 過濾出未分類的新聞
    unclassified_news = filter_new_news_only(news_data, classified_story_ids)
    
    # 如果沒有未分類的新聞，直接返回
    if not unclassified_news:
        print("\n🎯 所有新聞都已分類，無需執行分類")
        return {
            "message": "所有新聞都已分類，無需處理",
            "total_news": len(news_data.data),
            "unclassified_news": 0,
            "total_topics": len(topic_data.data)
        }
    
    # 為所有專題建立描述檔案（因為未分類的新聞可能分到任何專題）
    print(f"\n開始為所有 {len(topic_data.data)} 個專題建立描述檔案...")
    topic_profiles = build_topic_profiles(gemini, topic_data.data)
    
    # 準備專題候選清單
    print("準備專題候選清單...")
    topics_payload = build_topics_payload(topic_profiles, max_aliases=6)
    
    # 分類未分類的新聞
    print(f"開始分類 {len(unclassified_news)} 篇未分類新聞...")
    fake_news_data = type('obj', (object,), {'data': unclassified_news})
    classified_results = classify_all_news(gemini, fake_news_data, topics_payload, topic_profiles)
    
    # 分組結果
    print("分組結果...")
    grouped_output = group_results_by_topic(classified_results, topic_profiles)
    
    # 儲存結果到檔案
    out_path = save_results_to_file(grouped_output)
    print_summary(grouped_output, out_path)
    
    # 增量存入資料庫（不清除現有分類，只新增）
    db_summary = save_incremental_results_to_database(supabase, grouped_output)
    
    # 準備執行摘要
    execution_summary = {
        "total_topics": len(topic_data.data),
        "total_news": len(news_data),
        "unclassified_news": len(unclassified_news),
        "newly_classified": sum(len(t["stories"]) for t in grouped_output["topics"]),
        "topics_with_new_news": sum(1 for g in grouped_output["topics"] if g["stories"]),
        "unassigned_news": len(grouped_output["unassigned"]),
        "database_saved": db_summary["saved_count"],
        "database_failed": db_summary["failed_count"]
    }
    
    # 整合所有結果並保存為 JSON 檔案
    complete_results = {
        "timestamp": datetime.now().isoformat(),
        "execution_summary": execution_summary,
        "grouped_output": grouped_output,
        "file_path": str(out_path),
        "database_summary": db_summary
    }
    
    # 保存完整結果到 JSON 檔案
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)
    complete_results_path = out_dir / f"complete_results_{datetime.now():%Y%m%d_%H%M%S}.json"
    
    try:
        with open(complete_results_path, "w", encoding="utf-8") as f:
            json.dump(complete_results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整結果已保存至: {complete_results_path}")
    except Exception as e:
        print(f"❌ 保存完整結果失敗: {e}")
    
    return complete_results

# ========================================
# 執行點
# ========================================
if __name__ == "__main__":
    main()
