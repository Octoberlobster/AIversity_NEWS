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
CATEGORY_STYLE_HINTS = {
    "政治": "neutral editorial, cinematic realism",
    "社會": "documentary realism, human-centric",
    "國際": "cinematic realism with diplomatic symbolism (no flags)",
    "財經": "corporate realism with abstract financial props (no digits)",
    "科技": "modern tech realism with device/object focus (no UI text)",
}

DEFAULT_MODEL_ID = "gemini-2.0-flash-preview-image-generation"

def _safe_slug(text: str, maxlen: int = 60) -> str:
    ascii_text = unidecode((text or "").strip())
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"\s+", "-", ascii_text)
    return ascii_text[:maxlen] if ascii_text else "untitled"

def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def _load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    flat = []
    
    if isinstance(data, list):
        # 檢查是否為新格式 (包含 story_info 和 comprehensive_report)
        if data and isinstance(data[0], dict) and "story_info" in data[0] and "comprehensive_report" in data[0]:
            # 新格式：每個項目都是一個完整的報導
            for item in data:
                story_info = item.get("story_info", {})
                report = item.get("comprehensive_report", {})
                
                flat.append({
                    "story_title": story_info.get("story_title", ""),
                    "category": story_info.get("category", "misc"),
                    "article_title": report.get("title", "").replace("## ", "").replace("**", ""),  # 清理標題格式
                    "article_summary": report.get("content", "")[:500] + "..." if len(report.get("content", "")) > 500 else report.get("content", ""),  # 截取前500字作為摘要
                    "title": report.get("title", "").replace("## ", "").replace("**", ""),  # 相容舊格式
                    "summary": report.get("content", "")[:500] + "..." if len(report.get("content", "")) > 500 else report.get("content", ""),  # 相容舊格式
                    "content": report.get("content", ""),
                    "id": f"story_{story_info.get('story_index', 0)}",
                    "article_count": story_info.get("total_articles", 0)
                })
        else:
            # 舊格式：包含 stories 和 articles
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
        # 直接的 articles 格式
        flat = data.get("articles", [])
    
    return flat

def _prompt_photoreal_no_text(news_title: str, news_summary: str, category: str) -> str:
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

    # 針對新聞內容動態生成圖像描述 - 強調無文字視覺
    core_subject = (
        f"A scene representing the core concepts of the news: '{news_title}'. "
        f"The visual elements should metaphorically or symbolically illustrate the key points from the summary: '{news_summary}'. "
        f"Focus on generic, non-identifiable persons and symbolic objects to convey the narrative without any text. "
        f"Use pure visual elements: silhouettes, objects, colors, lighting, and composition to tell the story. "
        f"Examples: Use a clean gavel (no text) for legal stories, abstract geometric shapes for financial data, "
        f"or anonymous silhouettes for political discussions. All documents, screens, and signs should be blank or abstract."
    )

    # 強力禁止文字的設定 - 多重強調
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

    # 輸出限制 (保持不變)
    output_constraints = (
        "Square aspect ratio, high clarity, realistic textures and materials, "
        "no graphic overlays, no UI elements."
    )

    # 將所有部分組合在一起 - 文字禁令優先
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
    for attempt in range(1, retry_times + 1):
        try:
            resp = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    # 依官方規範，必須同時包含 TEXT 與 IMAGE 才會輸出圖片
                    response_modalities=['TEXT', 'IMAGE'],
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
    image = Image.open(BytesIO(img_bytes))
    image.save(out_path, format="PNG", optimize=True)

def _generate_image_description(news_title: str, news_summary: str, category: str) -> str:
    """
    為生成的圖片創建完整的說明文字（最多15字，確保句子完整）
    
    Args:
        news_title (str): 新聞標題
        news_summary (str): 新聞摘要
        category (str): 新聞類別
        
    Returns:
        str: 完整的圖片說明文字（最多15字，確保語句完整）
    """
    # 清理標題，移除無關標記和網站名稱
    title_clean = news_title.replace("| 政治", "").replace("｜ 公視新聞網 PNN", "")
    title_clean = title_clean.replace("｜", "").replace("|", "").replace("PNN", "")
    title_clean = title_clean.replace("公視新聞網", "").replace("新聞網", "")
    title_clean = title_clean.strip()
    
    # 識別關鍵元素
    people = []
    actions = []
    events = []
    
    # 人物識別
    if "柯文哲" in title_clean or "柯P" in title_clean:
        people.append("柯文哲")
    if "黃國昌" in title_clean:
        people.append("黃國昌")
    if "北檢" in title_clean:
        people.append("北檢")
    if "檢察官" in title_clean:
        people.append("檢察官")
    
    # 動作識別
    if "譴責" in title_clean:
        actions.append("譴責")
    if "暴走" in title_clean:
        actions.append("暴走")
    if "怒斥" in title_clean or "怒罵" in title_clean:
        actions.append("怒斥")
    
    # 事件識別
    if "開庭" in title_clean:
        events.append("開庭")
    if "休庭" in title_clean:
        events.append("休庭")
    
    # 生成完整句子的候選方案
    candidates = []
    
    # 方案1: 完整的主謂賓結構
    if people and actions:
        if len(people) >= 2:
            # A 動作 B
            sentence = f"{people[0]}{actions[0]}{people[1]}"
            if len(sentence) <= 15:
                candidates.append((sentence, 3))  # 高優先級
            
            # B 受到 A 的動作
            if "譴責" in actions:
                sentence = f"{people[1]}遭{people[0]}譴責"
                if len(sentence) <= 15:
                    candidates.append((sentence, 3))
        else:
            # 單一人物 + 動作 + 事件/對象
            base = f"{people[0]}{actions[0]}"
            if len(base) <= 15:
                candidates.append((base, 2))
                
                # 嘗試添加事件
                if events:
                    extended = f"{people[0]}{events[0]}{actions[0]}"
                    if len(extended) <= 15:
                        candidates.append((extended, 3))
    
    # 方案2: 事件描述
    if events and people:
        sentence = f"{events[0]}{people[0]}事件"
        if len(sentence) <= 15:
            candidates.append((sentence, 2))
    
    # 方案3: 直接使用標題中的完整短語
    import re
    # 按常見分隔符分割，找出完整短語
    separators = r'[：:，,。！!？?\s]'
    phrases = re.split(separators, title_clean)
    
    for phrase in phrases:
        phrase = phrase.strip()
        if 4 <= len(phrase) <= 15:  # 適當長度的完整短語
            candidates.append((phrase, 1))
    
    # 方案4: 智能截取，確保在合理位置截斷
    if not candidates:
        # 找出自然的截取點
        natural_breaks = ['，', ',', '。', '！', '!', '？', '?', '：', ':', ' ']
        
        for i in range(min(15, len(title_clean)), 3, -1):
            if i < len(title_clean) and title_clean[i] in natural_breaks:
                candidates.append((title_clean[:i], 1))
                break
            elif title_clean[i-1:i+1] not in ['檢察', '國昌', '文哲', '北檢']:
                # 確保不在常見詞彙中間截斷
                candidates.append((title_clean[:i], 1))
                break
    
    # 選擇最佳候選
    best = ""
    if candidates:
        # 按優先級排序，然後按長度（偏好較短的完整句子）
        candidates.sort(key=lambda x: (-x[1], len(x[0])))
        best = candidates[0][0].strip()
    else:
        # 如果沒有候選，使用前15個字符
        best = title_clean[:15]
        
    # 最終檢查：確保不以常見的不完整字詞結尾，並嘗試補全
    incomplete_endings = ['檢', '察', '國', '昌', '文', '哲', '的', '了', '在', '與', '北', '黃']
    while best and best[-1] in incomplete_endings and len(best) > 3:
        # 嘗試從原標題中找到更完整的版本
        if best.endswith('黃') and '黃國昌' in title_clean and len(best) + 2 <= 15:
            best = best + '國昌'
            break
        elif best.endswith('北') and '北檢' in title_clean and len(best) + 1 <= 15:
            best = best + '檢'
            break
        elif best.endswith('檢') and '檢察' in title_clean and len(best) + 1 <= 15:
            best = best + '察'
            break
        elif best.endswith('察') and '檢察官' in title_clean and len(best) + 1 <= 15:
            best = best + '官'
            break
        else:
            best = best[:-1].strip()
    
    return best

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
    讀取 JSON，批量生成「照片級寫實、無文字」的事件示意圖並存檔。

    參數：
      - input_json: JSON 檔路徑（支援 stories/articles 結構）
      - output_dir: 輸出資料夾
      - model_id: 模型 ID（預設 gemini-2.0-flash-preview-image-generation）
      - max_items: 限制處理的篇數，None 表示全量
      - max_images_per_article: 每篇生成張數
      - retry_times: 單張圖的生成重試次數
      - sleep_between_calls: 兩次 API 呼叫之間的節流秒數

    回傳：
      - dict，包含 processed, succeeded, failed, errors 概況
    """
    load_dotenv()
    _ensure_dir(output_dir)

    # 從環境讀 API Key（SDK 會自動讀取 GEMINI_API_KEY 或 GOOGLE_API_KEY）
    client = genai.Client()

    articles = _load_json(input_json)
    if max_items is not None:
        articles = articles[:max_items]

    errors = []
    processed = 0
    succeeded = 0
    failed = 0
    
    # 儲存圖片資訊的列表
    image_metadata = []

    for art in tqdm(articles, desc="Generating event illustrations", ncols=100):
        processed += 1
        title = art.get("article_title") or art.get("title") or "untitled"
        summary = art.get("article_summary") or art.get("summary") or art.get("content") or ""
        category = art.get("category") or art.get("story_category") or "misc"
        prompt = _prompt_photoreal_no_text(title, summary, category)

        cat_slug = _safe_slug(category, maxlen=40)
        out_category = os.path.join(output_dir, cat_slug)
        _ensure_dir(out_category)

        base_slug = _safe_slug(title, maxlen=70)
        article_ok = True

        for i in range(1, max_images_per_article + 1):
            out_name = f"{base_slug}_{i}.png" if max_images_per_article > 1 else f"{base_slug}.png"
            out_path = os.path.join(out_category, out_name)
            if os.path.exists(out_path):
                # 如果圖片已存在，也要加入metadata
                description = _generate_image_description(title, summary, category)
                image_metadata.append({
                    "image_path": out_path,
                    "description": description,
                    "article_title": title,
                    "category": category,
                    "article_id": art.get("id", ""),
                    "generated": False  # 表示這次沒有重新生成
                })
                continue

            img_bytes = _gen_image_bytes_with_retry(
                client, prompt, model_id, retry_times, sleep_between_calls
            )
            if not img_bytes:
                errors.append({"title": title, "category": category, "reason": "no_image"})
                article_ok = False
                continue

            try:
                _save_png(img_bytes, out_path)
                
                # 生成圖片說明
                description = _generate_image_description(title, summary, category)
                
                # 將圖片資訊加入metadata
                image_metadata.append({
                    "image_path": out_path,
                    "description": description,
                    "article_title": title,
                    "category": category,
                    "article_id": art.get("id", ""),
                    "generated": True  # 表示這次新生成的
                })
                
                time.sleep(sleep_between_calls)
            except (IOError, OSError) as e:
                errors.append({"title": title, "category": category, "reason": f"save_error: {e}"})
                article_ok = False

        if article_ok:
            succeeded += 1
        else:
            failed += 1

    # 錯誤落地
    if errors:
        err_path = os.path.join(output_dir, "errors.json")
        with open(err_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
    
    # 儲存圖片metadata到JSON檔案
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
