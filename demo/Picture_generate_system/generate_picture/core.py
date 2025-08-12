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

# 類別→寫實編輯語氣（不提供會誘發文字的元素）
# 此部分保持不變
CATEGORY_STYLE_HINTS = {
    "政治": "neutral editorial, cinematic realism",
    "社會": "documentary realism, human-centric",
    "國際": "cinematic realism with diplomatic symbolism (no flags)",
    "財經": "corporate realism with abstract financial props (no digits)",
    "科技": "modern tech realism with device/object focus (no UI text)",
}

DEFAULT_MODEL_ID = "gemini-2.0-flash-preview-image-generation"

def _safe_slug(text: str, maxlen: int = 60) -> str:
    # 此輔助函式保持不變
    ascii_text = unidecode((text or "").strip())
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"\s+", "-", ascii_text)
    return ascii_text[:maxlen] if ascii_text else "untitled"

def _ensure_dir(path: str):
    # 此輔助函式保持不變
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

# MODIFIED: _load_json 函式簡化，以直接讀取新的 JSON 結構
def _load_json(path: str) -> List[Dict[str, Any]]:
    """
    直接讀取指定的 JSON 檔案。
    假設檔案格式為包含故事物件的列表 (List of story objects)。
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []

def _prompt_photoreal_no_text(news_title: str, news_summary: str, category: str) -> str:
    # 此函式保持不變
    """
    根據新聞標題和摘要，生成不含文字的攝影級寫實事件示意圖提示。
    """
    category_styles = {
        "政治": "dramatic, serious, high-contrast, documentary style",
        "社會": "documentary realism, human-centric",
        "國際": "cinematic realism with diplomatic symbolism (no flags)",
        "財經": "neutral corporate tone, high-tech, clean aesthetics",
        "科技": "futuristic, sleek, innovative, digital aesthetics",
        "finance": "neutral corporate tone, high-tech, clean aesthetics",
        "politics": "dramatic, serious, high-contrast, documentary style",
        "technology": "futuristic, sleek, innovative, digital aesthetics",
        "sports": "dynamic, energetic, motion blur, emotional",
        "environment": "natural, hopeful, subtle textures, wide shots"
    }
    style_hint = category_styles.get(
        category or "", "neutral editorial tone with subtle cinematic realism"
    )
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
    core_subject = (
        f"A scene representing the core concepts of the news: '{news_title}'. "
        f"The visual elements should metaphorically or symbolically illustrate the key points from the summary: '{news_summary}'. "
        f"Focus on generic, non-identifiable persons and symbolic objects to convey the narrative without any text. "
        f"Use pure visual elements: silhouettes, objects, colors, lighting, and composition to tell the story. "
        f"Examples: Use a clean gavel (no text) for legal stories, abstract geometric shapes for financial data, "
        f"or anonymous silhouettes for political discussions. All documents, screens, and signs should be blank or abstract."
    )
    no_text = (
        "CRITICAL: Absolutely NO TEXT of any kind within the image. "
        "This is the most important requirement: NO letters, NO numbers, NO words, NO captions, NO labels, NO banners, NO signage, NO UI, NO subtitles. "
        "NO logos, NO trademarks, NO watermarks, NO brand marks, NO flags with text. "
        "NO Chinese characters, NO English letters, NO Arabic numerals, NO symbols that resemble text. "
        "Avoid any text-like or glyph-like patterns on clothing, props, documents, screens, newspapers, books, or backgrounds. "
        "If an element could contain text (documents, screens, boards, newspapers, books, signs, displays), render it completely blank, blurred, or use abstract geometric patterns instead. "
        "Replace any potential text areas with solid colors, abstract patterns, or blur effects. "
        "Focus on pure visual storytelling through objects, people, colors, and composition only. "
        "REMINDER: The image must be 100% text-free."
    )
    output_constraints = (
        "Square aspect ratio, high clarity, realistic textures and materials, "
        "no graphic overlays, no UI elements."
    )
    prompt = (
        f"IMPORTANT: {no_text} "
        f"Generate a scene representing: {core_subject}. "
        f"Style requirements: {style_hint}, {photo_style}. "
        f"Technical specs: {camera_tech}. "
        f"Lighting setup: {lighting}. "
        f"Output format: {output_constraints}. "
        f"FINAL REMINDER: Ensure the image contains absolutely no text, letters, numbers, or written characters of any kind."
    )
    return prompt

def _gen_image_bytes_with_retry(
    client: genai.Client,
    prompt: str,
    model_id: str,
    retry_times: int,
    sleep_between_calls: float
) -> Optional[bytes]:
    # 此函式保持不變
    for attempt in range(1, retry_times + 1):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                ),
            )
            cands = getattr(resp, "candidates", [])
            if not cands:
                raise RuntimeError("No candidates in response")
            img_bytes = None
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
                        except (ValueError, TypeError):
                            pass
            if img_bytes:
                return img_bytes
            time.sleep(sleep_between_calls)
        except (RuntimeError, ValueError, TypeError) as e:
            if attempt >= retry_times:
                print(f"[ERROR] generate failed after {retry_times} attempts: {e}")
                return None
            time.sleep(sleep_between_calls)
    return None

def _save_png(img_bytes: bytes, out_path: str):
    # 此函式保持不變
    image = Image.open(BytesIO(img_bytes))
    image.save(out_path, format="PNG", optimize=True)

def _generate_image_description(news_title: str, news_summary: str, category: str) -> str:
    # 此函式保持不變，它會根據傳入的標題和摘要生成描述
    """
    為生成的圖片創建完整的說明文字（最多15字，確保句子完整）
    """
    title_clean = news_title.replace("| 政治", "").replace("｜ 公視新聞網 PNN", "")
    title_clean = title_clean.replace("｜", "").replace("|", "").replace("PNN", "")
    title_clean = title_clean.replace("公視新聞網", "").replace("新聞網", "")
    title_clean = title_clean.strip()
    # 接下來的邏輯都與原版相同，此處省略以保持簡潔
    # ...
    # 為了程式碼的完整性，在此貼上原函式的其餘部分
    people = []
    actions = []
    events = []
    if "柯文哲" in title_clean or "柯P" in title_clean: people.append("柯文哲")
    if "黃國昌" in title_clean: people.append("黃國昌")
    if "北檢" in title_clean: people.append("北檢")
    if "檢察官" in title_clean: people.append("檢察官")
    if "譴責" in title_clean: actions.append("譴責")
    if "暴走" in title_clean: actions.append("暴走")
    if "怒斥" in title_clean or "怒罵" in title_clean: actions.append("怒斥")
    if "開庭" in title_clean: events.append("開庭")
    if "休庭" in title_clean: events.append("休庭")
    candidates = []
    if people and actions:
        if len(people) >= 2:
            sentence = f"{people[0]}{actions[0]}{people[1]}"
            if len(sentence) <= 15: candidates.append((sentence, 3))
            if "譴責" in actions:
                sentence = f"{people[1]}遭{people[0]}譴責"
                if len(sentence) <= 15: candidates.append((sentence, 3))
        else:
            base = f"{people[0]}{actions[0]}"
            if len(base) <= 15: candidates.append((base, 2))
            if events:
                extended = f"{people[0]}{events[0]}{actions[0]}"
                if len(extended) <= 15: candidates.append((extended, 3))
    if events and people:
        sentence = f"{events[0]}{people[0]}事件"
        if len(sentence) <= 15: candidates.append((sentence, 2))
    import re
    separators = r'[：:，,。！!？?\s]'
    phrases = re.split(separators, title_clean)
    for phrase in phrases:
        phrase = phrase.strip()
        if 4 <= len(phrase) <= 15: candidates.append((phrase, 1))
    if not candidates:
        natural_breaks = ['，', ',', '。', '！', '!', '？', '?', '：', ':', ' ']
        for i in range(min(15, len(title_clean)), 3, -1):
            if i < len(title_clean) and title_clean[i] in natural_breaks:
                candidates.append((title_clean[:i], 1))
                break
            elif title_clean[i-1:i+1] not in ['檢察', '國昌', '文哲', '北檢']:
                candidates.append((title_clean[:i], 1))
                break
    best = ""
    if candidates:
        candidates.sort(key=lambda x: (-x[1], len(x[0])))
        best = candidates[0][0].strip()
    else:
        best = title_clean[:15]
    incomplete_endings = ['檢', '察', '國', '昌', '文', '哲', '的', '了', '在', '與', '北', '黃']
    while best and best[-1] in incomplete_endings and len(best) > 3:
        if best.endswith('黃') and '黃國昌' in title_clean and len(best) + 2 <= 15:
            best = best + '國昌'
            break
        elif best.endswith('北') and '北檢' in title_clean and len(best) + 1 <= 15:
            best = best + '檢'
            break
        # ... (其他補全邏輯)
        else:
            best = best[:-1].strip()
    return best if best else (title_clean[:12] if len(title_clean) > 12 else title_clean)

# MODIFIED: 主要邏輯函式，以處理新的 JSON 格式和命名規則
def generate_from_json(
    input_json: str,
    output_dir: str,
    *,
    model_id: str = DEFAULT_MODEL_ID,
    max_items: Optional[int] = None,
    max_images_per_article: int = 1,
    retry_times: int = 3,
    sleep_between_calls: float = 0.6,
) -> Dict[str, Any]:
    """
    讀取新的 JSON 格式，批量生成圖片並根據 story_index 命名存檔。
    """
    load_dotenv()
    _ensure_dir(output_dir)
    client = genai.Client()

    # 使用修改後的 _load_json 讀取資料
    stories = _load_json(input_json)
    if max_items is not None:
        stories = stories[:max_items]

    errors = []
    processed = 0
    succeeded = 0
    failed = 0
    image_metadata = []

    # 迴圈遍歷每個 "story" 物件
    for story in tqdm(stories, desc="Generating event illustrations", ncols=100):
        processed += 1
        
        # --- 數據讀取邏輯修改 ---
        story_info = story.get("story_info", {})
        report = story.get("comprehensive_report", {})
        
        # 標題: 從 comprehensive_report.title 讀取
        title = report.get("title", "untitled")
        # 摘要: 從 comprehensive_report.versions.long 讀取
        summary = report.get("versions", {}).get("long", "")
        # 分類: 從 story_info.category 讀取
        category = story_info.get("category", "misc")
        # 索引: 從 story_info.story_index 讀取，用於命名
        story_index = story_info.get("story_index")
        
        if story_index is None:
            errors.append({"title": title, "reason": "missing_story_index"})
            failed += 1
            continue

        prompt = _prompt_photoreal_no_text(title, summary, category)

        cat_slug = _safe_slug(category, maxlen=40)
        out_category = os.path.join(output_dir, cat_slug)
        _ensure_dir(out_category)
        
        # --- 圖片命名規則修改 ---
        # 使用 story_index 作為檔名基礎
        base_name = str(story_index)
        
        article_ok = True
        for i in range(1, max_images_per_article + 1):
            # 如果每篇只生成一張圖，檔名為 "story_index.png"
            # 如果生成多張，則為 "story_index_1.png", "story_index_2.png", ...
            out_name = f"{base_name}_{i}.png" if max_images_per_article > 1 else f"{base_name}.png"
            out_path = os.path.join(out_category, out_name)

            if os.path.exists(out_path):
                # 如果圖片已存在，也要加入 metadata
                description = _generate_image_description(title, summary, category)
                rel_path = os.path.relpath(out_path, output_dir)
                image_metadata.append({
                    "image_path": rel_path,
                    "description": description,
                    "article_title": title,
                    "category": category,
                    "article_id": str(story_index), # 使用 story_index 作為 ID
                    "generated": False
                })
                continue

            img_bytes = _gen_image_bytes_with_retry(
                client, prompt, model_id, retry_times, sleep_between_calls
            )

            if not img_bytes:
                errors.append({"title": title, "story_index": story_index, "reason": "no_image"})
                article_ok = False
                continue

            try:
                _save_png(img_bytes, out_path)
                description = _generate_image_description(title, summary, category)
                rel_path = os.path.relpath(out_path, output_dir)
                image_metadata.append({
                    "image_path": rel_path,
                    "description": description,
                    "article_title": title,
                    "category": category,
                    "article_id": str(story_index), # 使用 story_index 作為 ID
                    "generated": True
                })
                time.sleep(sleep_between_calls)
            except (IOError, OSError) as e:
                errors.append({"title": title, "story_index": story_index, "reason": f"save_error: {e}"})
                article_ok = False
        
        if article_ok:
            succeeded += 1
        else:
            failed += 1

    # 錯誤和 metadata 的儲存邏輯保持不變
    if errors:
        err_path = os.path.join(output_dir, "errors.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)

    metadata_path = os.path.join(output_dir, "image_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_images": len(image_metadata),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "images": image_metadata
        }, f, ensure_ascii=False, indent=2)
    
    return {
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "errors_count": len(errors),
        "output_dir": output_dir,
        "metadata_path": metadata_path,
        "total_images": len(image_metadata)
    }

