import os
import json
import time
import re
from io import BytesIO
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from unidecode import unidecode
from PIL import Image
from tqdm import tqdm

from google import genai
from google.genai import types

# ============ 可調整區 ============
INPUT_JSON = "cleaned_final_news1.json"   # 請將附件放在與本檔同層
OUTPUT_DIR = "generated_images_test5"     # 測試輸出資料夾
MODEL_ID = "gemini-2.0-flash-preview-image-generation"
MAX_ITEMS = 5                              # 僅跑前5篇
MAX_IMAGES_PER_ARTICLE = 1                # 每篇1張
RETRY_TIMES = 3
SLEEP_BETWEEN_CALLS = 0.5
# ==================================

# 依類別提供事件示意風格方向（避免產生文字，人物以通用人像處理）
CATEGORY_STYLE_HINTS = {
    "政治": "clean editorial illustration with neutral palette, courtroom or press context implied by props",
    "社會": "modern flat illustration focusing on generic people and key objects in public settings",
    "國際": "cinematic moody scene with symbolic objects representing diplomacy or conflict, no flags",
    "財經": "business-themed illustration using abstract charts (no text), briefcase, coins as icons",
    "科技": "futuristic illustration with devices and abstract UI panels (no text)",
}

def safe_slug(text: str, maxlen: int = 60) -> str:
    ascii_text = unidecode((text or "").strip())
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"\s+", "-", ascii_text)
    return ascii_text[:maxlen] if ascii_text else "untitled"

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    flat = []
    if isinstance(data, list):
        for story in data:
            story_title = story.get("story_title")
            category = story.get("category")
            for art in story.get("articles", []):
                flat.append({
                    "story_title": story_title,
                    "category": category,
                    **art
                })
    else:
        flat = data.get("articles", [])
    return flat

def summarize_for_prompt(article: Dict[str, Any]) -> str:
    """
    事件示意圖（提煉精華→影像意象→寫實無文字）：
    - 從內文擷取最精華的「人/物/場景/情緒/動作」要素，轉為純影像化描述
    - 僅以人物或物件意象呈現（generic, non-identifiable persons / symbolic objects）
    - 嚴禁任何文字、字母、數字、商標、水印、旗幟、UI、字幕、看板字樣
    - 偏向攝影級寫實（photorealistic）
    """
    import re

    category = article.get("category") or article.get("story_category") or ""
    content = (article.get("content") or "").strip()

    # 1) 提煉文章精華（非常簡化且保守）：抓取可能代表事件本質的名詞/動作線索
    # - 避免長句與抽象詞，偏向「可視化的人/物/場景/動作」詞彙
    # - 若你的環境允許，可換用更進階的關鍵詞抽取；此處給出純內建的保守做法
    #   規則：抓取常見可視化物件/場景/行為詞（可依你的資料集擴充）
    keywords_bank = [
        # 人物與角色
        "judge", "lawyer", "reporter", "protester", "police", "official",
        "businessperson", "engineer", "doctor", "student",
        # 物件與道具
        "gavel", "microphone", "documents", "briefcase", "scales", "handcuffs",
        "camera", "laptop", "smartphone", "contract", "chart", "coin",
        # 場景與地點
        "courtroom", "press room", "office", "street", "podium", "meeting room",
        "server room", "lab", "airport",
        # 動作與姿態
        "speaking", "signing", "walking", "pointing", "gesturing", "presenting",
        "negotiating", "inspecting",
        # 情緒與氛圍
        "serious", "tense", "calm", "focused", "concerned",
    ]

    # 將內容轉小寫，粗略掃描關鍵詞
    text = content.lower()
    found = []
    for kw in keywords_bank:
        # 允許單複數或簡單變形，可依需要擴充
        pattern = r"\b" + re.escape(kw) + r"(s|es)?\b"
        if re.search(pattern, text):
            found.append(kw)
    # 精簡相似詞、去重，最多保留5個意象詞
    unique_visual_cues = []
    for w in found:
        if w not in unique_visual_cues:
            unique_visual_cues.append(w)
        if len(unique_visual_cues) >= 5:
            break

    # 若文章太難抽取，提供保底意象（避免空白導致模型產生文字）
    if not unique_visual_cues:
        unique_visual_cues = ["generic person", "documents", "microphone", "office"]

    # 2) 類別風格引導（沿用既有 CATEGORY_STYLE_HINTS）
    style_hint = CATEGORY_STYLE_HINTS.get(
        category,
        "neutral editorial tone with subtle cinematic realism"
    )

    # 3) 攝影級寫實參數與構圖
    photo_style = (
        "photorealistic, realistic photo, cinematic still, natural color grading, "
        "soft directional lighting, subtle film grain, shallow depth of field, creamy bokeh, "
        "subject isolation, rule of thirds, foreground/background layering"
    )
    camera_tech = (
        "full-frame look, 35mm lens, f/1.8 aperture, ISO 200, 1/250s shutter, "
        "shot on tripod, high dynamic range, accurate skin tones"
    )
    lighting = (
        "soft key light with gentle rim light, golden hour ambience or soft overcast, "
        "physically plausible shadows and reflections"
    )

    # 4) 嚴格無文字（多角度冗餘）
    no_text = (
        "Absolutely no text of any kind within the image. "
        "No letters, numbers, words, captions, labels, banners, signs, UI, or subtitles. "
        "No logos, trademarks, watermarks, brand marks, or flags. "
        "Avoid any text-like or glyph-like patterns on clothing, props, backgrounds, or screens. "
        "If an element could contain text (documents, screens, boards), render it blank or abstract."
    )

    # 5) 人物/物件要求（不可辨識）
    people_objects = (
        "Focus on generic, non-identifiable persons (faceless or simplified features, "
        "silhouette or back/side view) and key symbolic objects."
    )

    # 6) 將精華意象合併為「純影像化清單」（不給標題、不給摘要長句）
    visual_keywords = ", ".join(unique_visual_cues)

    output_constraints = (
        "Square aspect ratio, high clarity, realistic textures, natural materials, "
        "no text overlays, no graphic UI elements."
    )

    prompt = (
        f"Create an {style_hint} {photo_style}. "
        f"Use {camera_tech}. "
        f"Lighting: {lighting}. "
        f"{people_objects} "
        f"Key visual cues (non-textual): {visual_keywords}. "
        f"{no_text} "
        f"{output_constraints}"
    )
    return prompt




def gen_image_bytes_with_retry(client: genai.Client, prompt: str) -> Optional[bytes]:
    for attempt in range(1, RETRY_TIMES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                ),
            )
            cands = getattr(resp, "candidates", [])
            if not cands:
                raise RuntimeError("No candidates in response")

            img_bytes = None
            # 僅保存圖片 part；忽略文字 part
            for part in cands[0].content.parts:
                if getattr(part, "inline_data", None):
                    data = part.inline_data.data
                    if isinstance(data, (bytes, bytearray)):
                        img_bytes = bytes(data)
                        break
                    else:
                        try:
                            import base64
                            img_bytes = base64.b64decode(data)
                            break
                        except Exception:
                            pass
            if img_bytes:
                return img_bytes
            time.sleep(1.0)
        except Exception as e:
            if attempt >= RETRY_TIMES:
                print(f"[ERROR] generate failed after {RETRY_TIMES} attempts: {e}")
                return None
            time.sleep(1.5)
    return None

def save_png(img_bytes: bytes, out_path: str):
    image = Image.open(BytesIO(img_bytes))
    image.save(out_path, format="PNG", optimize=True)

def main():
    load_dotenv()
    ensure_dir(OUTPUT_DIR)
    client = genai.Client()  # 從 GEMINI_API_KEY 或 GOOGLE_API_KEY 讀取

    articles = load_json(INPUT_JSON)
    articles = articles[:MAX_ITEMS] if MAX_ITEMS else articles

    errors = []
    print(f"Testing first {len(articles)} articles...")

    for art in tqdm(articles, desc="Generating event illustrations (first-5, no-text)", ncols=100):
        title = art.get("article_title") or art.get("title") or "untitled"
        category = art.get("category") or art.get("story_category") or "misc"
        prompt = summarize_for_prompt(art)

        cat_slug = safe_slug(category, maxlen=40)
        out_dir = os.path.join(OUTPUT_DIR, cat_slug)
        ensure_dir(out_dir)

        base_slug = safe_slug(title, maxlen=70)
        for i in range(1, MAX_IMAGES_PER_ARTICLE + 1):
            out_name = f"{base_slug}_{i}.png" if MAX_IMAGES_PER_ARTICLE > 1 else f"{base_slug}.png"
            out_path = os.path.join(out_dir, out_name)
            if os.path.exists(out_path):
                continue

            img_bytes = gen_image_bytes_with_retry(client, prompt)
            if not img_bytes:
                errors.append({"title": title, "category": category, "reason": "no_image"})
                continue

            try:
                save_png(img_bytes, out_path)
            except Exception as e:
                errors.append({"title": title, "category": category, "reason": f"save_error: {e}"})

            time.sleep(SLEEP_BETWEEN_CALLS)

    if errors:
        err_path = os.path.join(OUTPUT_DIR, "errors_first5.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        print(f"Completed with errors: {len(errors)}. See {err_path}")
    else:
        print("First-5 no-text test done without errors.")

if __name__ == "__main__":
    main()
