from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime as dt
from datetime import datetime
import requests
from supabase import create_client, Client
import uuid
import os
import json
import random
import re
from urllib.parse import urljoin, urlparse
from collections import defaultdict

# === Supabase 設定 ===
SUPABASE_URL = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Chrome options 設定
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

def download_images_from_soup(soup, final_url, article_id, base_folder="images"):
    """從 BeautifulSoup 物件中下載圖片"""
    images_info = []
    
    # 建立圖片資料夾
    article_folder = os.path.join(base_folder, article_id)
    os.makedirs(article_folder, exist_ok=True)
    
    # 尋找圖片標籤
    img_tags = soup.find_all('img')
    
    # 常見的新聞圖片選擇器
    news_selectors = [
        'img[src*="upload"]',
        'article img',
        '.content img',
        '.article-content img',
        '.story img',
        'figure img',
        '.image img',
        '.photo img'
    ]
    
    # 嘗試用更精確的選擇器找新聞圖片
    news_images = []
    for selector in news_selectors:
        found_imgs = soup.select(selector)
        news_images.extend(found_imgs)
    
    # 如果找不到特定的新聞圖片，使用所有圖片但過濾更嚴格
    if not news_images:
        news_images = img_tags
    
    print(f"   🖼️  找到 {len(news_images)} 個圖片標籤")
    
    downloaded_count = 0
    
    for i, img in enumerate(news_images):
        try:
            # 獲取圖片URL
            img_url = (img.get('src') or 
                      img.get('data-src') or 
                      img.get('data-lazy-src') or
                      img.get('data-original'))
            
            if not img_url or img_url.startswith('data:'):
                continue
            
            # 處理相對路徑
            img_url = urljoin(final_url, img_url)
            
            # 過濾掉明顯的廣告或小圖片
            if any(keyword in img_url.lower() for keyword in ['ad', 'banner', 'logo', 'icon', 'avatar']):
                continue
            
            # 檢查圖片尺寸屬性
            width = img.get('width')
            height = img.get('height')
            if width and height:
                try:
                    if int(width) < 200 or int(height) < 200:
                        continue
                except:
                    pass
            
            # 下載圖片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': final_url
            }
            
            img_response = requests.get(img_url, headers=headers, timeout=10)
            img_response.raise_for_status()
            
            # 檢查內容大小，過濾太小的圖片
            if len(img_response.content) < 5000:  # 小於 5KB
                continue
            
            # 獲取檔案副檔名
            parsed_url = urlparse(img_url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename or '.' not in filename:
                # 根據 content-type 決定副檔名
                content_type = img_response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'
                filename = f"image_{i}{ext}"
            
            # 儲存圖片
            filepath = os.path.join(article_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # 記錄圖片資訊
            images_info.append({
                "filename": filename,
                "url": img_url,
                "local_path": filepath,
                "size": len(img_response.content)
            })
            
            downloaded_count += 1
            print(f"     ✅ 下載圖片: {filename}")
            
            # 避免過於頻繁的請求
            time.sleep(0.3)
            
        except Exception as e:
            print(f"     ❌ 下載圖片失敗: {e}")
    
    print(f"   📊 總共下載了 {downloaded_count} 張圖片")
    return images_info

def get_main_story_links(main_url, category):
    """步驟 1: 從主頁抓取所有主要故事連結"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    story_links = []
    
    try:
        print(f"🔍 正在抓取 {category} 領域的主要故事連結...")
        driver.get(main_url)
        
        # 等待頁面載入 - 找到所有 c-wiz 區塊
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'c-wiz[jsrenderer="jeGyVb"]')))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        c_wiz_blocks = soup.find_all("c-wiz", {"jsrenderer": "jeGyVb"})
        
        print(f"✅ 找到 {len(c_wiz_blocks)} 個 c-wiz 區塊")
        
        # 從每個 c-wiz 區塊中找到主要故事連結
        for i, block in enumerate(c_wiz_blocks, start=1):
            story_link = block.find("a", class_="jKHa4e")  # 主要故事連結
            
            if story_link:
                href = story_link.get("href")
                title = story_link.text.strip()
                print(f"   處理故事 {i}: {href}")
                
                if href:
                    # 處理相對連結
                    if href.startswith("./"):
                        full_link = "https://news.google.com" + href[1:]
                    else:
                        full_link = "https://news.google.com" + href
                    
                    story_links.append({
                        "index": i,
                        "title": title,
                        "url": full_link,
                        "category": category  # 新增：將分類資訊加入
                    })
                    
                    print(f"{i}. 📰 [{category}] {title}")
                    print(f"   🔗 {full_link}")
        
        print(f"\n📊 總共收集到 {len(story_links)} 個 {category} 領域的主要故事連結")
        
    except Exception as e:
        print(f"❌ 抓取主要故事連結時出錯: {e}")
    finally:
        driver.quit()
    
    return story_links

def get_article_links_from_story(story_info):
    """步驟 2: 進入每個故事頁面，找出所有 a tag class="VDXfz" 的 href"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    article_links = []
    
    try:
        print(f"\n🔍 正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
        driver.get(story_info['url'])
        time.sleep(random.randint(3, 6))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 找到所有 h4 tag class="ipQwMb ekueJc RD0gLb" 
        h4_elements = soup.find_all("h4", class_="ipQwMb ekueJc RD0gLb")
        
        print(f"   ✅ 找到 {len(h4_elements)} 個 h4 元素")
        
        for j, h4 in enumerate(h4_elements, start=1):
            # if j > 5:
            #     break  # 最多只抓取 5 篇文章    
            
            # 在 h4 下面找 a tag class="DY5T1d RZIKme"
            link = h4.find("a", class_="DY5T1d RZIKme")
            
            if link:
                href = link.get("href")
                link_text = link.text.strip()
                
                if href:
                    # 處理相對連結
                    if href.startswith("./"):
                        full_href = "https://news.google.com" + href[1:]
                    else:
                        full_href = "https://news.google.com" + href
                    
                    article_links.append({
                        "story_index": story_info['index'],
                        "story_title": story_info['title'],
                        "story_category": story_info['category'],  # 新增：保存故事分類
                        "article_index": j,
                        "article_title": link_text,
                        "article_url": full_href
                    })
                    
                    print(f"     {j}. 📄 {link_text}")
                    print(f"        🔗 {full_href}")
            else:
                print(f"     {j}. ❌ h4 元素中沒有找到對應的 a tag")
        
    except Exception as e:
        print(f"❌ 處理故事時出錯: {e}")
    finally:
        driver.quit()
    
    return article_links

def extract_publish_time(soup, final_url):
    """從網頁中提取發布時間"""
    publish_time = None
    
    # 常見的時間選擇器和屬性
    time_selectors = [
        # JSON-LD 結構化數據
        'script[type="application/ld+json"]',
        # HTML5 time 標籤
        'time[datetime]',
        'time[pubdate]',
        # 常見的時間 class
        '.publish-time',
        '.published-time',
        '.article-time',
        '.post-time',
        '.date',
        '.timestamp',
        '.article-date',
        '.publish-date',
        '.post-date',
        '.entry-date',
        # Meta 標籤
        'meta[property="article:published_time"]',
        'meta[name="publish_date"]',
        'meta[name="article:published_time"]',
        'meta[name="pubdate"]',
        'meta[name="date"]',
        # 特定新聞網站
        '.story-meta time',
        '.byline time',
        '.article-meta time',
        '.news-meta time'
    ]
    
    for selector in time_selectors:
        try:
            elements = soup.select(selector)
            
            for element in elements:
                time_text = None
                
                if selector == 'script[type="application/ld+json"]':
                    # 處理 JSON-LD
                    try:
                        json_content = json.loads(element.string)
                        if isinstance(json_content, list):
                            json_content = json_content[0]
                        
                        # 查找日期欄位
                        date_fields = ['datePublished', 'publishedDate', 'dateCreated', 'dateModified']
                        for field in date_fields:
                            if field in json_content:
                                time_text = json_content[field]
                                break
                    except:
                        continue
                
                elif element.name == 'meta':
                    # Meta 標籤
                    time_text = element.get('content')
                
                elif element.name == 'time':
                    # Time 標籤
                    time_text = element.get('datetime') or element.get_text().strip()
                
                else:
                    # 其他元素
                    time_text = element.get_text().strip()
                
                if time_text:
                    # 嘗試解析時間
                    parsed_time = parse_time_string(time_text)
                    if parsed_time:
                        publish_time = parsed_time
                        print(f"   ⏰ 找到發布時間: {publish_time} (來源: {selector})")
                        return publish_time
        
        except Exception as e:
            continue
    
    # 如果都找不到，嘗試用正則表達式在文本中尋找
    try:
        text_content = soup.get_text()
        
        # 常見的時間格式正則表達式
        time_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\T]\d{1,2}:\d{2})',  # YYYY-MM-DD HH:MM
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # MM-DD-YYYY 或 DD-MM-YYYY
            r'發布時間[：:\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\T]?\d{0,2}:?\d{0,2})',
            r'更新時間[：:\s]*(\d{4}[-/]\d{1,2}[-/]\d{1,2}[\s\T]?\d{0,2}:?\d{0,2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日[\s]*\d{0,2}:?\d{0,2})',  # 中文格式
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                time_text = matches[0]
                parsed_time = parse_time_string(time_text)
                if parsed_time:
                    print(f"   ⏰ 從文本中找到時間: {parsed_time}")
                    return parsed_time
    
    except Exception as e:
        pass
    
    print(f"   ⚠️  無法找到發布時間")
    return None

def parse_time_string(time_str):
    """解析各種格式的時間字符串"""
    if not time_str:
        return None
    
    # 清理時間字符串
    time_str = str(time_str).strip()
    
    # 移除時區信息（簡化處理）
    time_str = re.sub(r'[+-]\d{2}:?\d{2}$', '', time_str)
    time_str = re.sub(r'[A-Z]{3,4}$', '', time_str)
    
    # 常見的時間格式
    formats = [
        '%Y-%m-%dT%H:%M:%S',      # ISO 格式
        '%Y-%m-%d %H:%M:%S',      # 標準格式
        '%Y-%m-%d %H:%M',         # 沒有秒
        '%Y-%m-%d',               # 只有日期
        '%Y/%m/%d %H:%M:%S',      # 斜線分隔
        '%Y/%m/%d %H:%M',         # 斜線分隔，沒有秒
        '%Y/%m/%d',               # 斜線分隔，只有日期
        '%d/%m/%Y %H:%M:%S',      # 歐洲格式
        '%d/%m/%Y %H:%M',         # 歐洲格式，沒有秒
        '%d/%m/%Y',               # 歐洲格式，只有日期
        '%m/%d/%Y %H:%M:%S',      # 美國格式
        '%m/%d/%Y %H:%M',         # 美國格式，沒有秒
        '%m/%d/%Y',               # 美國格式，只有日期
    ]
    
    # 處理中文日期格式
    if '年' in time_str and '月' in time_str and '日' in time_str:
        try:
            # 提取數字
            year_match = re.search(r'(\d{4})年', time_str)
            month_match = re.search(r'(\d{1,2})月', time_str)
            day_match = re.search(r'(\d{1,2})日', time_str)
            time_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
            
            if year_match and month_match and day_match:
                year = int(year_match.group(1))
                month = int(month_match.group(1))
                day = int(day_match.group(1))
                
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    return datetime(year, month, day, hour, minute).strftime('%Y/%m/%d %H:%M')
                else:
                    return datetime(year, month, day).strftime('%Y/%m/%d')
        except:
            pass
    
    # 嘗試各種格式
    for fmt in formats:
        try:
            parsed_dt = datetime.strptime(time_str, fmt)
            return parsed_dt.strftime('%Y/%m/%d %H:%M') if '%H' in fmt else parsed_dt.strftime('%Y/%m/%d')
        except:
            continue
    
    return None

def get_final_content(article_info, driver):
    """步驟 3: 跳轉到原始網站並抓取內容、圖片和時間"""
    try:
        driver.get(article_info['article_url'])
        time.sleep(random.randint(4, 8))
        
        # 取得跳轉後的真實網址
        final_url = driver.current_url
        print(f"   最終網址: {final_url}")
        
        # 取得 HTML 原始碼並交給 BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # 清理內容
        if soup.body:
            body_content = str(soup.body)
            body_content = body_content.replace("\x00", "").replace("\r", "").replace("\n", "")
            body_content = body_content.replace('"', '\\"')
            
            # 生成文章 ID
            article_id = str(uuid.uuid4())
            
            # === 新增：提取發布時間 ===
            print(f"   ⏰ 開始提取發布時間...")
            publish_time = extract_publish_time(soup, final_url)
            
            # === 新增：下載圖片 ===
            print(f"   🖼️  開始下載圖片...")
            images_info = download_images_from_soup(soup, final_url, article_id)
            
            return {
                "id": article_id,
                "story_index": article_info['story_index'],
                "story_title": article_info['story_title'],
                "story_category": article_info['story_category'],  # 新增：保存分類
                "article_index": article_info['article_index'],
                "article_title": article_info['article_title'],
                "google_news_url": article_info['article_url'],
                "final_url": final_url,
                "crawl_date": dt.datetime.now().strftime("%Y/%m/%d %H:%M"),  # 爬取時間
                "publish_date": publish_time,  # 新增：文章發布時間
                "content": body_content,
                "images": images_info  # 新增：圖片資訊
            }
        
    except Exception as e:
        print(f"     ❌ 無法取得內容: {e}")
    
    return None

def main():
    """主執行函式"""
    # 定義要爬取的新聞領域
    topic_sources = [
        {
            "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFZ4ZERBU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
            "category": "政治"
        },
        {
            "url": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
            "category": "科學與科技"
        }
        # 可以繼續添加更多領域...
        # {
        #     "url": "其他 Google News 主題 URL",
        #     "category": "其他領域名稱"
        # }
    ]
    
    # 建立必要的資料夾
    os.makedirs("json", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    
    # 用於跟蹤全局故事索引
    global_story_index = 1
    all_article_links = []
    
    # === 步驟 1 & 2: 遍歷所有主題領域 ===
    print("=== 開始爬取多個新聞領域 ===")
    
    for topic in topic_sources:
        main_url = topic["url"]
        category = topic["category"]
        
        print(f"\n=== 處理主題：{category} ===")
        
        # 步驟 1: 找到該領域的主要故事連結
        story_links = get_main_story_links(main_url, category)
        
        if not story_links:
            print(f"❌ 沒有找到 {category} 領域的任何主要故事連結")
            continue
        
        # 步驟 2: 從每個故事抓取文章連結
        print(f"\n=== 從 {category} 領域的每個故事抓取文章連結 ===")
        
        for story in story_links[:8]:  # 可視需求修改數量
            # 更新為全局索引
            story['index'] = global_story_index
            
            article_links = get_article_links_from_story(story)
            all_article_links.extend(article_links)
            
            global_story_index += 1
            time.sleep(2)
    
    # 儲存文章連結（非必要，可註解）
    with open("json/article_links.json", "w", encoding="utf-8") as f:
        json.dump(all_article_links, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 所有文章連結已儲存到 article_links.json (總共 {len(all_article_links)} 個)")

    # === 步驟 3: 抓取文章內容和圖片 ===
    print("\n=== 步驟 3: 抓取文章內容和圖片 ===")
    final_articles = []

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://news.google.com/")  # 必須先訪問一次才能加 cookie
    time.sleep(2)

    # 匯入 cookies（如果存在）
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies:
            if 'sameSite' in cookie:
                cookie.pop('sameSite')
            driver.add_cookie(cookie)
    except FileNotFoundError:
        print("⚠️  cookies.json 檔案不存在，繼續執行...")

    # 處理文章
    for i, article in enumerate(all_article_links[:40], start=1):  # 限制40篇文章
        print(f"\n處理文章 {i}/{min(40, len(all_article_links))}")
        print(f"   [{article.get('story_category', '未知')}] {article['article_title']}")
        
        content = get_final_content(article, driver)
        
        if content:
            final_articles.append(content)
            print(f"✅ 成功抓取: [{content['story_category']}] {content['article_title']}")
            print(f"   📷 圖片數量: {len(content['images'])}")
        else:
            print(f"❌ 無法取得內容")
            
        time.sleep(1)

    driver.quit()

    if not final_articles:
        print("❌ 沒有成功抓取到任何文章內容")
        return

    # === 依 story_index 分組並包含分類資訊 ===
    grouped = defaultdict(list)

    for item in final_articles:
        grouped[item["story_index"]].append({
            "id": item["id"],
            "article_index": item["article_index"],
            "article_title": item["article_title"],
            "google_news_url": item["google_news_url"],
            "final_url": item["final_url"],
            "crawl_date": item["crawl_date"],
            "publish_date": item["publish_date"],
            "content": item["content"],
            "images": item["images"]
        })

    grouped_articles = []
    for story_index in sorted(grouped.keys()):
        # 從 final_articles 中找到對應的故事資訊
        sample_article = next((x for x in final_articles if x["story_index"] == story_index), None)
        if sample_article:
            story_title = sample_article["story_title"]
            story_category = sample_article["story_category"]
        else:
            story_title = ""
            story_category = "未知"
            
        grouped_articles.append({
            "story_index": story_index,
            "story_title": story_title,
            "category": story_category,  # 新增：分類資訊
            "articles": grouped[story_index]
        })

    # === 儲存分組 JSON ===
    with open("json/final_news.json", "w", encoding="utf-8") as f:
        json.dump(grouped_articles, f, ensure_ascii=False, indent=2)

    # === 統計資訊 ===
    total_images = sum(len(article['images']) for article in final_articles)
    category_stats = defaultdict(int)
    for article in final_articles:
        category_stats[article['story_category']] += 1

    print(f"\n🎉 完成！總共成功抓取 {len(final_articles)} 篇文章")
    print("📊 各領域文章數量統計:")
    for category, count in category_stats.items():
        print(f"   {category}: {count} 篇")
    print(f"📷 總共下載 {total_images} 張圖片")
    print("📁 儲存檔案:")
    print("   - json/final_news.json（依 story_index 分組，包含領域分類和圖片資訊）")
    print("   - json/article_links.json（所有文章連結）")
    print("   - images/ 資料夾（依文章 ID 分類的圖片）")

if __name__ == "__main__":
    main()