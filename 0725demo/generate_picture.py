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
INPUT_JSON = "cleaned_final_news1.json"   # JSON 檔案路徑
OUTPUT_DIR = "generated_images"           # 全量輸出資料夾
MODEL_ID = "gemini-2.0-flash-preview-image-generation"
MAX_ITEMS = None                          # None 代表全量處理
MAX_IMAGES_PER_ARTICLE = 1                # 每篇生成張數
RETRY_TIMES = 3
SLEEP_BETWEEN_CALLS = 0.6                 # 節流，視配額調整
# ==================================

# 類別→寫實編輯語氣（避免提供會誘發文字的元素）
CATEGORY_STYLE_HINTS = {
    "政治": "neutral editorial, cinematic realism",
    "社會": "documentary realism, human-centric",
    "國際": "cinematic realism with diplomatic symbolism (no flags)",
    "財經": "corporate realism with abstract financial props (no digits)",
    "科技": "modern tech realism with device/object focus (no UI text)",
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

def generate_news_image_prompt(news_title: str, news_summary: str, category: str) -> str:
    """
    根據新聞標題和摘要，生成不含文字的攝影級寫實事件示意圖提示。
    
    Args:
        news_title (str): 新聞標題，用於增加圖像相關性。
        news_summary (str): 新聞摘要或內容，用於具體化圖像元素。
        category (str): 新聞類別，用於調整風格提示。
        
    Returns:
        str: 完整的圖像生成提示。
    """
    
    # 根據類別設定風格提示
    CATEGORY_STYLE_HINTS = {
        "finance": "neutral corporate tone, high-tech, clean aesthetics",
        "politics": "dramatic, serious, high-contrast, documentary style",
        "technology": "futuristic, sleek, innovative, digital aesthetics",
        "sports": "dynamic, energetic, motion blur, emotional",
        "environment": "natural, hopeful, subtle textures, wide shots"
    }
    style_hint = CATEGORY_STYLE_HINTS.get(
        category or "", "neutral editorial tone with subtle cinematic realism"
    )

    # 固定攝影風格與技術設定
    photo_style = (
        "photorealistic, realistic photo, cinematic still, natural color grading, "
        "soft directional lighting, subtle film grain, shallow depth of field, creamy bokeh, "
        "subject isolation, rule of thirds, foreground/background layering"
    )
    camera_tech = "full-frame look, 35mm lens, f/1.8, ISO 200, 1/250s shutter, high dynamic range"
    lighting = (
        "soft key light with gentle rim light, golden hour ambience or soft overcast, "
        "physically plausible shadows and reflections"
    )

    # 針對新聞內容動態生成圖像描述
    # 這裡將新聞標題和摘要作為圖像的「核心主題」
    core_subject = (
        f"A scene representing the core concepts of the news: '{news_title}'. "
        f"The visual elements should metaphorically or symbolically illustrate the key points from the summary: '{news_summary}'. "
        f"Focus on generic, non-identifiable persons and symbolic objects to convey the narrative. "
        f"Example: Use a blurred gavel for a legal report, an abstract graph for a financial story, or silhouettes of people talking for a political debate."
    )

    # 強力禁止文字的設定 (保持不變)
    no_text = (
        "Absolutely no text of any kind within the image. "
        "No letters, numbers, words, captions, labels, banners, signage, UI, or subtitles. "
        "No logos, trademarks, watermarks, brand marks, or flags. "
        "Avoid any text-like or glyph-like patterns on clothing, props, documents, screens, or backgrounds. "
        "If an element could contain text (documents, screens, boards), render it blank or abstract."
    )

    # 輸出限制 (保持不變)
    output_constraints = (
        "Square aspect ratio, high clarity, realistic textures and materials, "
        "no graphic overlays, no UI elements."
    )

    # 將所有部分組合在一起
    prompt = (
        f"{core_subject}. "
        f"Style: {style_hint}, {photo_style}. "
        f"Camera: {camera_tech}. "
        f"Lighting: {lighting}. "
        f"{no_text}. "
        f"{output_constraints}."
    )
    
    return prompt

def gen_image_bytes_with_retry(client: genai.Client, prompt: str) -> Optional[bytes]:
    for attempt in range(1, RETRY_TIMES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # 根據官方規範，必須同時要求 TEXT 與 IMAGE 才能輸出圖片
                    response_modalities=['TEXT', 'IMAGE'],  # 必填[3][1][2]
                ),
            )
            cands = getattr(resp, "candidates", [])
            if not cands:
                raise RuntimeError("No candidates in response")

            img_bytes = None
            # 僅保存圖片 part；完全忽略文字 part
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
    client = genai.Client()  # 自動從 GEMINI_API_KEY / GOOGLE_API_KEY 讀取

    articles = load_json(INPUT_JSON)
    if MAX_ITEMS is not None:
        articles = articles[:MAX_ITEMS]

    errors = []
    total = len(articles)
    print(f"Total articles to process: {total}")

    for art in tqdm(articles, desc="Generating event illustrations (all)", ncols=100):
        title = art.get("article_title") or art.get("title") or "untitled"
        category = art.get("category") or art.get("story_category") or "misc"
        summary = art.get("article_summary") or art.get("summary") or art.get("content") or ""
        prompt = generate_news_image_prompt(title, summary, category)

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
        err_path = os.path.join(OUTPUT_DIR, "errors_all.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        print(f"Completed with errors: {len(errors)}. See {err_path}")
    else:
        print("All done without errors.")

if __name__ == "__main__":
    main()
