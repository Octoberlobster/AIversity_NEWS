from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import hashlib
from supabase import create_client, Client
import os 

# Supabase 設定
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "YOUR_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_article_text(page, selectors=None):
    """
    嘗試多種選擇器來取得文章內容
    """
    if selectors is None:
        selectors = [
            "div.article-content",
            "article",
            "div.content",
            "div.post-content",
            "div.entry-content", 
            "main article",
            "div.story-body",
            "div.article-body",
            "[class*='content']",
            "[class*='article']",
            "p"  # 最後嘗試所有段落
        ]
    
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    
    # 移除不需要的元素
    for unwanted in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        unwanted.decompose()
    
    # 依序嘗試不同的選擇器
    for selector in selectors:
        try:
            elements = soup.select(selector)
            if elements:
                # 如果是 p 標籤，取所有段落文字
                if selector == "p":
                    text = " ".join([p.get_text(strip=True) for p in elements if len(p.get_text(strip=True)) > 20])
                else:
                    # 取第一個匹配元素或所有匹配元素的文字
                    text = " ".join([el.get_text(strip=True) for el in elements])
                
                if text and len(text) > 50:  # 確保有足夠內容
                    print(f"    使用選擇器: {selector}, 內容長度: {len(text)}")
                    return text
        except Exception as e:
            continue
    
    print(f"    所有選擇器都無法取得內容")
    return ""

def get_hash(text: str):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# 從 Supabase 拿前 300 筆 stories
response = supabase.table("stories").select("story_id, story_url").order("crawl_date", desc=True).limit(300).execute()
stories = response.data

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    hash_map = {}  # hash -> 第一個發現的URL
    duplicate_groups = {}  # hash -> [所有相同內容的URLs]
    processed_urls = set()  # 避免重複處理相同URL

    # 遍歷每個 story_url
    for story in stories:
        url = story["story_url"]
        
        # 如果已經處理過這個URL就跳過
        if url in processed_urls:
            continue

        # 先取前 89 個字元，做候選比對
        url_prefix = url[:89]

        # 找出 Supabase 中所有有相同 prefix 的 URL (包含自己)
        prefix_matches = [
            s for s in stories if s["story_url"][:89] == url_prefix
        ]

        if len(prefix_matches) <= 1:
            print(f"URL {url} 沒有相似的前綴，跳過")
            processed_urls.add(url)
            continue

        print(f"找到 {len(prefix_matches)} 篇相同前綴文章，開始抓取內容...")

        # 對所有相同前綴的文章進行內容抓取
        prefix_hashes = {}
        
        for match_story in prefix_matches:
            match_url = match_story["story_url"]
            story_id = match_story["story_id"]
            
            # 標記為已處理
            processed_urls.add(match_url)
            
            try:
                # 在 URL 後面加上 &so=1 參數
                if '?' in match_url:
                    crawl_url = f"{match_url}&so=1"
                else:
                    crawl_url = f"{match_url}?so=1"
                
                print(f"正在抓取: {match_url}")
                print(f"  實際請求: {crawl_url}")
                
                # 增加重試機制和更多等待時間
                page.goto(crawl_url, wait_until="domcontentloaded", timeout=30000)
                
                # 等待頁面載入完成
                page.wait_for_timeout(2000)  # 等待 2 秒讓動態內容載入
                
                # 嘗試等待常見的文章容器出現
                try:
                    page.wait_for_selector("article, [class*='content'], [class*='article']", timeout=5000)
                except:
                    pass  # 如果等不到也沒關係，繼續嘗試抓取
                
                text = get_article_text(page)
                
                if not text:
                    print(f"  -> 無法取得內容，可能是：")
                    print(f"     - 需要登入的頁面")
                    print(f"     - 動態載入內容")
                    print(f"     - 反爬蟲機制")
                    print(f"     - 頁面結構特殊")
                    continue
                    
                h = get_hash(text)
                
                # 記錄所有相同內容的URL
                if h in duplicate_groups:
                    duplicate_groups[h].append({
                        'story_id': story_id,
                        'story_url': match_url
                    })
                    print(f"  -> 發現重複！與已存在的 {len(duplicate_groups[h])} 篇文章內容相同")
                else:
                    duplicate_groups[h] = [{
                        'story_id': story_id,
                        'story_url': match_url
                    }]
                    print(f"  -> 新內容，雜湊: {h[:8]}... (長度: {len(text)} 字元)")
                    
            except Exception as e:
                print(f"  -> 處理 {match_url} 出錯: {e}")

        # 將這組前綴的結果合併到全域 hash_map
        for h, urls_list in duplicate_groups.items():
            if len(urls_list) > 1:
                if h not in hash_map:
                    hash_map[h] = urls_list[0]['story_url']

    browser.close()

print(f"\n=== 重複文章檢測結果 ===")
print(f"處理了 {len(processed_urls)} 個獨特URL")

# 列出所有重複的文章群組
duplicate_found = False
duplicate_count = 0

for content_hash, urls_list in duplicate_groups.items():
    if len(urls_list) > 1:
        duplicate_found = True
        duplicate_count += len(urls_list) - 1  # 重複數量 = 總數 - 1
        
        print(f"\n重複群組 {content_hash[:8]}... (共 {len(urls_list)} 篇):")
        for i, item in enumerate(urls_list):
            status = "原始" if i == 0 else "重複"
            print(f"  [{status}] Story ID: {item['story_id']}")
            print(f"         URL: {item['story_url']}")

if not duplicate_found:
    print("沒有發現重複的文章！")
else:
    print(f"\n=== 總結 ===")
    print(f"- 獨特內容數量：{len([h for h, urls in duplicate_groups.items() if len(urls) >= 1])}")
    print(f"- 重複文章總數：{duplicate_count}")
    print(f"- 重複群組數量：{len([h for h, urls in duplicate_groups.items() if len(urls) > 1])}")

    # 僅列出重複的 story_url 清單
    print(f"\n=== 所有重複的 story_url 清單 ===")
    all_duplicate_urls = []
    for content_hash, urls_list in duplicate_groups.items():
        if len(urls_list) > 1:
            # 除了第一個（原始）之外都是重複的
            for item in urls_list[1:]:
                all_duplicate_urls.append(item['story_url'])
                print(f"{item['story_url']}")
    
    print(f"\n總共 {len(all_duplicate_urls)} 個重複的 URL")