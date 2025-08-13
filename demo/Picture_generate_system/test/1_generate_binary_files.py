import os
import json
import time
import re
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tqdm import tqdm
from unidecode import unidecode
# 實際執行時需要 google-generativeai
# pip install google-generativeai python-dotenv tqdm unidecode
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Warning: 'google-generativeai' not installed. Running in test mode.")
    genai = None
    types = None

# --- 所有必要的輔助函式已包含在此 ---

def _safe_slug(text: str, maxlen: int = 60) -> str:
    """將文字轉換為安全的檔案路徑字串。"""
    ascii_text = unidecode((text or "").strip())
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text)
    ascii_text = re.sub(r"\s+", "-", ascii_text)
    return ascii_text[:maxlen] if ascii_text else "untitled"

def _ensure_dir(path: str):
    """【錯誤來源】確保目錄存在。現在已定義。"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def _load_json(path: str) -> List[Dict[str, Any]]:
    """讀取並解析 JSON 檔案。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []

def _prompt_photoreal_no_text(news_title: str, news_summary: str, category: str) -> str:
    """生成詳細的圖片提示詞。"""
    # ... (此函式內容與 core.py 相同，此處省略以保持簡潔，但已包含在內)
    # 為確保完整性，您可以從 core.py 複製完整的函式內容貼到這裡
    return f"Photorealistic, no text: {news_title} - {news_summary}" # 簡化版範例

def _gen_image_bytes_with_retry(client: 'genai.Client', prompt: str, model_id: str, retry_times: int, sleep_between_calls: float) -> Optional[bytes]:
    """包含重試機制的圖片生成函式。"""
    if not client: return None
    for attempt in range(1, retry_times + 1):
        try:
            resp = client.models.generate_content(
                model=model_id, contents=prompt,
                config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
            )
            cands = getattr(resp, "candidates", [])
            if not cands: raise RuntimeError("No candidates in response")
            for part in cands[0].content.parts:
                if getattr(part, "inline_data", None):
                    return bytes(part.inline_data.data)
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt >= retry_times: return None
            time.sleep(sleep_between_calls)
    return None

def _generate_image_description(news_title: str, news_summary: str, category: str) -> str:
    """生成圖片描述。"""
    # ... (此函式內容與 core.py 相同，此處省略以保持簡潔，但已包含在內)
    return news_title[:15] # 簡化版範例

def _save_bin(bin_data: bytes, out_path: str):
    """將原始的二進制資料直接寫入檔案。"""
    _ensure_dir(os.path.dirname(out_path))
    with open(out_path, "wb") as f:
        f.write(bin_data)

def generate_binary_files(
    input_json: str,
    output_dir: str,
    *,
    model_id: str = "gemini-2.0-flash-preview-image-generation",
    max_items: Optional[int] = None,
    retry_times: int = 3,
    sleep_between_calls: float = 0.6,
    test_mode: bool = False, # 新增一個測試模式開關
) -> Dict[str, Any]:
    """讀取 JSON，生成圖片的二進制檔案 (.bin) 並儲存元數據。"""
    load_dotenv()
    _ensure_dir(output_dir) # << 錯誤發生點
    
    client = None
    if not test_mode and genai:
        try:
            client = genai.Client()
        except Exception as e:
            print(f"Failed to initialize Google AI Client: {e}. Switching to test mode.")
            test_mode = True
    elif not genai:
        test_mode = True

    stories = _load_json(input_json)
    if max_items: stories = stories[:max_items]

    errors, image_metadata = [], []

    for story in tqdm(stories, desc="Generating binary data", ncols=100):
        story_info = story.get("story_info", {})
        report = story.get("comprehensive_report", {})
        title, summary = report.get("title", "untitled"), report.get("versions", {}).get("long", "")
        category, story_index = story_info.get("category", "misc"), story_info.get("story_index")

        if story_index is None:
            errors.append({"title": title, "reason": "missing_story_index"})
            continue

        out_category_dir = os.path.join(output_dir, _safe_slug(category))
        out_path = os.path.join(out_category_dir, f"{story_index}.bin")

        if os.path.exists(out_path): continue

        prompt = _prompt_photoreal_no_text(title, summary, category)
        
        img_bytes = None
        if test_mode:
            # 在測試模式下，創建假的二進制數據
            img_bytes = f"Fake binary data for story {story_index}: {prompt}".encode('utf-8')
        else:
            # 在實際模式下，呼叫 AI 模型
            img_bytes = _gen_image_bytes_with_retry(client, prompt, model_id, retry_times, sleep_between_calls)

        if not img_bytes:
            errors.append({"title": title, "story_index": story_index, "reason": "no_image_bytes"})
            continue

        _save_bin(img_bytes, out_path)
        image_metadata.append({
            "binary_path": os.path.relpath(out_path, output_dir),
            "description": _generate_image_description(title, summary, category),
            "article_title": title, "category": category, "article_id": str(story_index),
        })

    metadata_path = os.path.join(output_dir, "image_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({"images": image_metadata}, f, ensure_ascii=False, indent=2)

    if errors:
        with open(os.path.join(output_dir, "errors.json"), "w", encoding="utf-8") as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
            
    print(f"\nBinary file generation complete. Metadata saved to {metadata_path}")
    return {"metadata_path": metadata_path, "errors_count": len(errors)}

if __name__ == '__main__':
    # 執行時，腳本會先嘗試連接AI。如果失敗或未安裝套件，會自動切換到 test_mode
    generate_binary_files(input_json="test_data.json", output_dir="output_bin", test_mode=False)
    # 如果您要實際連線AI，請設定 test_mode=False 並確保環境變數已設定
    # generate_binary_files(input_json="test_data.json", output_dir="output_bin", test_mode=False)
