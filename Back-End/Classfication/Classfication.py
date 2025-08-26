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

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
topic = supabase.table("topic").select("topic_id, topic_title").execute()
news = supabase.table("single_news").select("story_id, news_title, short").execute()

# ========= 1) 專題簡述輸出結構：≤120 字 =========
class TopicBrief(BaseModel):
    short_description: str = Field(max_length=120)
    aliases: list[str] = Field(default_factory=list)

# ========= 1.1) 分類階段 LLM 回覆的最小結構 =========
class LMLabel(BaseModel):
    topic_id: Optional[str] = None
    topic_title: Optional[str] = None

# ========= 2) 產生簡述的提示詞 =========
def build_prompt(topic_title: str) -> str:
    return f"""專題標題：{topic_title}
規則：
- 允許上網檢索近 3–5 年公開資料以釐清定義與常見範圍。
- 只輸出 JSON；欄位：
  - short_description：請控制在 100–110 字（最多 120 字），1–2 句，說明本專題的主題邊界與常見範圍。
  - aliases：常見別名（可含中/英縮寫）。
- 若初稿超長，請自行刪減至不超過 120 字；不得空值。
- 避免寫入單一事件或單一公司。
"""

# ========= 3) 長度策略：理想 100–110，硬上限 120 =========
def clamp_desc(s: str, min_len: int = 100, max_len: int = 110, hard_max: int = 120) -> str:
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

# ========= 4) 從文字中抽出 JSON 候選 =========
def extract_json_candidate(text: str) -> Optional[str]:
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

# ========= 5) 校正重試（不開工具 → 強制 JSON 輸出） =========
def repair_to_json(gemini_client, bad_text: str) -> TopicBrief:
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
    fixed.short_description = clamp_desc(fixed.short_description, 100, 110, 120)
    return fixed

# ============================ 主流程：建立 topic_profiles ============================
topic_profiles: dict[str, dict] = {}
for item in topic.data:
    topic_title = item["topic_title"]

    # 第一次：開工具（允許上網），但不鎖 JSON MIME
    resp = gemini.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=build_prompt(topic_title),
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
            desc = clamp_desc(data.get("short_description", ""), 100, 110, 120)
            aliases = data.get("aliases", []) or []
            brief = TopicBrief(short_description=desc, aliases=aliases)
        except Exception:
            brief = None

    if brief is None:
        try:
            brief = repair_to_json(gemini, raw if raw else f'{{"short_description": "本專題：{topic_title}", "aliases": []}}')
        except Exception:
            brief = None

    if brief is None:
        fallback = f"本專題聚焦「{topic_title}」，彙整近年相關政策、事件、產業與社會影響，提供脈絡要點與趨勢觀察，協助讀者快速掌握重點與延伸討論。"
        brief = TopicBrief(short_description=clamp_desc(fallback, 100, 110, 120), aliases=[])

    print(f"[{topic_title}] {brief.short_description} (len={len(brief.short_description)}) | aliases={brief.aliases}")
    tid = str(item["topic_id"])
    topic_profiles[tid] = {
        "title": topic_title,
        "desc": brief.short_description,
        "aliases": brief.aliases,
    }

# ============================ 準備候選清單（全清單 + 可重現亂序） ============================
def build_topics_payload_full(topic_profiles: dict[str, dict], max_aliases: int = 6) -> list[dict]:
    items = []
    for tid, prof in topic_profiles.items():
        aliases = [a.strip() for a in (prof.get("aliases") or []) if a and a.strip()]
        aliases = aliases[:max_aliases]
        items.append({
            "topic_id": tid,
            "title": prof.get("title", ""),
            "desc": prof.get("desc", ""),
            "aliases": aliases,
        })
    return items

def shuffle_for_story(topics_payload: list[dict], story_id: str) -> list[dict]:
    seed = int(hashlib.md5(story_id.encode("utf-8")).hexdigest(), 16) % (10**8)
    rnd = random.Random(seed)
    copied = topics_payload[:]
    rnd.shuffle(copied)
    return copied

ALL_TOPICS_PAYLOAD = build_topics_payload_full(topic_profiles, max_aliases=6)

# ============================ 分類提示（要求只輸出 JSON） ============================
NEWS_MAX_CHARS = 1200
def build_classify_prompt_json(story_title: str, story_short: str, topics_payload: list[dict]) -> str:
    article = (story_title or "").strip()
    if story_short:
        article += "\n\n" + (story_short or "").strip()
    article = article[:NEWS_MAX_CHARS]

    topics_json = json.dumps(topics_payload, ensure_ascii=False)

    return (
        "任務：根據『候選專題清單』與『本文』，在候選中選出最合適的一個專題；"
        "若全部不合適，請回 null。\n"
        "輸出：僅輸出 JSON，且**必須完全符合**此結構（不可有多餘欄位或文字）：\n"
        '{\"topic_id\": <UUID或null>, \"topic_title\": <字串或null>}\n'
        "規則：\n"
        "1) 只能從候選清單中選；不可發明清單外的標籤。\n"
        "2) 若皆不合適：topic_id = null、topic_title = null。\n"
        "3) topic_title 請對應所選 topic_id 的 title。\n\n"
        f"【候選專題清單（JSON 陣列）】\n{topics_json}\n\n"
        f"【本文】\n標題：{story_title}\n內容摘錄：\n{article}\n"
    )

# ========= robust 解析器：確保永遠回 LMLabel =========
def safe_label_from_response(resp) -> LMLabel:
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

# ============================ 全量分類 ============================
classified_results: list[dict] = []
SKIP_NONE = False
errors = 0

for doc in news.data:
    sid = str(doc["story_id"])
    s_title = (doc.get("news_title") or "").strip()
    s_short = (doc.get("short") or "").strip()

    if not (s_title or s_short):
        if not SKIP_NONE:
            classified_results.append({
                "topic_id": None,
                "topic_title": None,
                "source_story": {"story_id": sid, "news_title": s_title, "short": s_short},
            })
        print(f"[story_id={sid}]（空文本） → topic_id=NONE")
        continue

    candidates = shuffle_for_story(ALL_TOPICS_PAYLOAD, sid)
    prompt = build_classify_prompt_json(s_title, s_short, candidates)

    # 不開工具，才能安全使用 JSON schema
    try:
        resp = gemini.models.generate_content(
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
        errors += 1
        label = LMLabel(topic_id=None, topic_title=None)
        print(f"[story_id={sid}] LLM 呼叫失敗：{e} → topic_id=NONE")

    # 以 topic_id 為準，避免模型把 title 打錯；用你的 canonical title 覆寫
    tid = label.topic_id if (label.topic_id and label.topic_id in topic_profiles) else None
    ttitle = topic_profiles[tid]["title"] if tid else None

    result_obj = {
        "topic_id": tid,
        "topic_title": ttitle,
        "source_story": {
            "story_id": sid,
            "news_title": s_title,
            "short": s_short,
        }
    }

    if (tid is None) and SKIP_NONE:
        pass
    else:
        classified_results.append(result_obj)

    shown = tid if tid else "NONE"
    print(f"[story_id={sid}] {s_title}\n  → topic_id={shown}")

# ====== 依 topic 分組並輸出（一次看全部） ======
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

out_dir = Path("out")
out_dir.mkdir(exist_ok=True)
out_path = out_dir / f"classified_grouped_{datetime.now():%Y%m%d_%H%M%S}.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(grouped_output, f, ensure_ascii=False, indent=2)

topics_with_stories = sum(1 for g in grouped_output["topics"] if g["stories"])
print(f"\n✅ 已輸出分組結果：共 {len(grouped_output['topics'])} 個主題（其中 {topics_with_stories} 個有分到文章），未分類 {len(unassigned)} 則 → {out_path}")
