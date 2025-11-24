import requests
from bs4 import BeautifulSoup
from typing import List
from env import supabase, gemini_client
from typing import List, Dict, Any, Optional
from google.genai import types
import json
import uuid

def craw_cna_topic() -> List[str]:
    """
    爬取 https://www.cna.com.tw/list/newstopic.aspx 頁面，
    取得前三個 <li> 中 <span> 的文字，回傳為字串清單（最多 3 項）。
    若發生錯誤或找不到則回傳空清單。
    """
    url = "https://www.cna.com.tw/list/newstopic.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"craw_cna_topic: 無法取得頁面: {e}")
        return []

    # 適當設定編碼並解析
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    ul = soup.find("ul", id="jsMainList")
    if not ul:
        return results

    for li in ul.find_all("li", recursive=False)[:3]:
        span = li.find("span")
        if span:
            text = span.get_text(strip=True)
            if text:
                results.append(text)

    return results

def craw_mnews_categories() -> List[str]:
    """
    爬取 https://www.mnews.tw/ 頁面，
    取得所有 class 包含 "category-nav__link nav-items_highlight__WbSDW" 的 <a> 標籤文字，回傳字串清單。
    若發生錯誤或找不到則回傳空清單。
    """
    url = "https://www.mnews.tw/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"craw_mnews_categories: 無法取得頁面: {e}")
        return []

    resp.encoding = resp.apparent_encoding or "utf-8"
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"craw_mnews_categories: 無法解析頁面: {e}")
        return []

    results = []
    # CSS selector: 同時包含兩個 class 的 <a>
    anchors = soup.select("a.category-nav__link.nav-items_highlight__WbSDW")
    for a in anchors:
        text = a.get_text(strip=True)
        if text:
            results.append(text)

    return results

def craw_pts_nav() -> List[str]:
    """
    爬取 https://news.pts.org.tw/ ，取得所有 li.ga-nav-menu 下
    a 標籤中 style 包含 color:#CA3E50 或 color:#2B6197 的文字，回傳字串清單。
    若發生錯誤或找不到則回傳空清單。
    """
    import re
    from bs4 import FeatureNotFound

    url = "https://news.pts.org.tw/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"craw_pts_nav: 無法取得頁面: {e}")
        return []

    resp.encoding = resp.apparent_encoding or "utf-8"
    try:
        soup = BeautifulSoup(resp.text, "lxml")
    except FeatureNotFound:
        soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    lis = soup.find_all("li", class_="ga-nav-menu")
    if not lis:
        return results

    pattern = re.compile(r"color\s*:\s*#(?:CA3E50|2B6197)", re.I)
    for li in lis:
        for a in li.find_all("a"):
            style = a.get("style", "")
            if style and pattern.search(style):
                text = a.get_text(strip=True)
                if text:
                    results.append(text)

    return results

def dedupe_topics_with_gemini(all_topics: List[str]) -> List[str]:
    """
    使用 Gemini 去重 all_topics，要求回傳 JSON 陣列的唯一項目（保留原始出現順序）。
    若呼叫失敗或回傳無法解析，回傳原始列表經過 Python 去重（保留順序）的結果。
    """
    if not all_topics:
        return []

    system_instruction = (
        "你是一個資料處理助手。請接收一個字串陣列，移除重複項目或相似項目，像是普發1萬和普發一萬和普發現金視為相同項目。"
        "保留原始出現順序，並僅以 JSON 陣列的格式輸出結果（例如: [\"項目A\", \"項目B\"]）。"
        "不要輸出額外文字或說明。"
    )

    user_prompt = json.dumps(all_topics, ensure_ascii=False)

    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
            }
        )
        text = getattr(resp, "text", None) or resp
        unique = json.loads(text)
        if isinstance(unique, list):
            return unique
    except Exception as e:
        print(f"dedupe_topics_with_gemini: 呼叫 Gemini 失敗: {e}")

    # fallback: Python 去重並保留順序
    seen = set()
    deduped = []
    for t in all_topics:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped

def fetch_topic_titles_from_supabase() -> List[str]:
    """
    從 Supabase 的 `topic` 表抓取所有 `topic_title`，回傳字串清單。
    若發生錯誤或沒資料則回傳空清單。
    """
    try:
        resp = supabase.table("topic").select("topic_title").execute()
        data = getattr(resp, "data", None)
        if not data:
            return []
        titles = []
        for row in data:
            title = row.get("topic_title")
            if title:
                titles.append(title)
        return titles
    except Exception as e:
        print(f"fetch_topic_titles_from_supabase: 無法取得資料: {e}")
        return []

def sync_topics_with_supabase(all_topics: List[str], supabase_titles: List[str]) -> None:
    """
    使用 Gemini 比對 all_topics 和 supabase_titles，
    1. 將相似標題統一成 supabase_titles 的格式
    2. 更新 supabase topic 表中的 alive 欄位
    - 若標題仍在 all_topics 出現，設為 1
    - 若標題已不在 all_topics，設為 0
    3. 新增不存在於 supabase 的新標題
    """
    if not all_topics or not supabase_titles:
        return

    system_instruction = """
    你是一個文字比對專家。請比對兩個標題列表：
    1. 將 topics 中的標題與 supabase_titles 比對
    2. 若發現相似標題（例：普發1萬 vs 普發一萬 vs 普發現金），從 topics 中移除該標題
    3. 輸出 JSON 格式：{
        "alive_status": {
            "supabase標題1": true/false,  # 表示該標題是否出現在topics中
            "supabase標題2": true/false
        },
        "new_topics": ["完全新的topics，不存在於也不相似於supabase_titles中的標題"]
    }
    請確保 new_topics 中的標題與 supabase_titles 中的任何標題都不相似。
    """

    user_prompt = json.dumps({
        "topics": all_topics,
        "supabase_titles": supabase_titles or []
    }, ensure_ascii=False)

    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
            }
        )
        
        result = json.loads(resp.text)
        
        # 更新 supabase topic 表的 alive 欄位
        for title in supabase_titles:
            is_alive = result["alive_status"].get(title, False)
            try:
                supabase.table("topic").update({"alive": 1 if is_alive else 0}).eq("topic_title", title).execute()
                print(f"已更新 topic '{title}' 的 alive 狀態為: {1 if is_alive else 0}")
            except Exception as e:
                print(f"更新 topic '{title}' 狀態失敗: {e}")

        # 新增不存在的標題
        for new_title in result.get("new_topics", []):
            try:
                new_topic = {
                    "topic_id": str(uuid.uuid4()),
                    "topic_title": new_title,
                    "alive": 1
                }
                supabase.table("topic").upsert(new_topic).execute()
                print(f"已新增新 topic: {new_title}")
            except Exception as e:
                print(f"新增 topic '{new_title}' 失敗: {e}")

        return result.get("new_topics", [])

    except Exception as e:
        print(f"呼叫 Gemini 或更新資料庫時發生錯誤: {e}")
        return []

if __name__ == "__main__":
    topics = craw_cna_topic()
    print("CNA topics:", topics)
    mnews_cats = craw_mnews_categories()
    print("MNews categories:", mnews_cats)
    pts_navs = craw_pts_nav()
    print("PTS navs:", pts_navs)

    all_topics = topics + mnews_cats + pts_navs
    print("All topics/categories:", all_topics) 

    # all_topics = ['颱風鳳凰', '非洲豬瘟', '藝人躲兵役案', '普發一萬', '蔡英文柏林行', '黃國昌爭議', '仁勳台積電', '颱風鳳凰', '普發1萬']
    unique_topics = dedupe_topics_with_gemini(all_topics)
    print("Unique topics/categories:", unique_topics)

    supabase_titles = fetch_topic_titles_from_supabase()
    print("Supabase topic titles:", supabase_titles)

    matched_topics = sync_topics_with_supabase(unique_topics, supabase_titles)
    print("統一後的 topics:", matched_topics)