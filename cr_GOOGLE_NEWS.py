from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime as dt
from datetime import datetime, timedelta
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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("⚠️ Supabase 未設定，將跳過重複檢查功能")

# Chrome options 設定
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-web-security")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--page-load-strategy=eager")

# 用戶代理
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

# 防止被識別為自動化
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# 廣告和追蹤阻擋
chrome_options.add_argument("--disable-background-timer-throttling")
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--disable-renderer-backgrounding")
chrome_options.add_argument("--disable-features=TranslateUI")
chrome_options.add_argument("--disable-ipc-flooding-protection")

# 圖片和媒體優化
chrome_options.add_argument("--disable-background-media")
chrome_options.add_argument("--disable-background-downloads")
chrome_options.add_argument("--aggressive-cache-discard")
chrome_options.add_argument("--disable-sync")

# 網路優化
chrome_options.add_argument("--disable-default-apps")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-plugins")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")

# 記憶體和效能優化
chrome_options.add_argument("--memory-pressure-off")
chrome_options.add_argument("--max_old_space_size=4096")
chrome_options.add_argument("--single-process")
chrome_options.add_argument("--no-zygote")

# 阻擋特定內容類型
prefs = {
    "profile.default_content_setting_values": {
        "notifications": 2,  # 阻擋通知
        "plugins": 2,        # 阻擋插件
        "popups": 2,         # 阻擋彈出窗口
        "geolocation": 2,    # 阻擋位置請求
        "media_stream": 2,   # 阻擋攝像頭/麥克風
    },
    "profile.managed_default_content_settings": {
        "images": 2,         # 1=允許, 2=阻擋圖片
    },
    "profile.default_content_settings": {
        "popups": 2
    }
}
chrome_options.add_experimental_option("prefs", prefs)

def check_story_exists_in_supabase(story_url, category):
    """
    檢查story_url是否已經在Supabase中存在
    如果存在且crawl_date在三天內，則返回True（跳過）
    如果存在但crawl_date超過三天，則返回False（需要重新爬取）
    如果不存在，則返回False（需要爬取）
    
    Returns:
        tuple: (should_skip, message, is_old_story)
            - should_skip (bool): True表示跳過，False表示需要爬取
            - message (str): 說明信息
            - is_old_story (bool): True表示是舊故事（超過3天），False表示新故事或不存在
    """
    if not supabase:
        return False, "Supabase未設定", False
    
    try:
        # 假設您的表名為 'stories'，請根據實際情況修改
        response = supabase.table('stories').select('*').eq('story_url', story_url).eq('category', category).execute()
        
        if not response.data:
            return False, "故事不存在於資料庫中，需要爬取", False
        
        # 取得最新的記錄
        latest_record = max(response.data, key=lambda x: x['crawl_date'])
        crawl_date_str = latest_record['crawl_date']
        
        # 解析crawl_date（假設格式為 "2024/01/15 10:30"）
        try:
            crawl_date = datetime.strptime(crawl_date_str, "%Y/%m/%d %H:%M")
        except ValueError:
            # 如果日期格式不匹配，嘗試其他格式
            try:
                crawl_date = datetime.fromisoformat(crawl_date_str.replace('Z', '+00:00'))
            except:
                return False, "無法解析crawl_date，需要重新爬取", False
        
        # 計算時間差
        current_time = datetime.now()
        time_difference = current_time - crawl_date
        
        if time_difference.days >= 3:
            return False, f"上次爬取時間超過3天（{time_difference.days}天前），需要重新爬取3天內新聞", True
        else:
            return True, f"上次爬取時間在3天內（{time_difference.days}天前），跳過", False
            
    except Exception as e:
        print(f"❌ 檢查Supabase時發生錯誤: {e}")
        return False, "檢查資料庫時發生錯誤，默認進行爬取", False

def parse_article_datetime(datetime_str):
    """
    解析文章的datetime字符串為datetime對象
    
    Args:
        datetime_str (str): 文章的datetime字符串 (例如: "2025-08-15T12:55:21Z")
        
    Returns:
        datetime or None: 解析成功返回datetime對象，失敗返回None
    """
    if not datetime_str or datetime_str == "未知時間":
        return None
    
    try:
        # 優先處理 ISO 格式 (例如: "2025-08-15T12:55:21Z")
        if 'T' in datetime_str:
            # 處理帶 Z 結尾的 UTC 時間
            if datetime_str.endswith('Z'):
                # 移除 Z 並轉換為 UTC 格式
                datetime_str = datetime_str.replace('Z', '+00:00')
            
            # 使用 fromisoformat 解析
            dt = datetime.fromisoformat(datetime_str)
            
            # 如果有時區信息，轉換為本地時間（移除時區信息）
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            
            return dt
        else:
            # 嘗試其他常見格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y-%m-%d",
                "%Y/%m/%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
    except Exception as e:
        print(f"⚠️ 解析時間格式失敗: {datetime_str}, 錯誤: {e}")
    
    return None

def is_article_within_days(article_datetime_str, days=3):
    """
    檢查文章是否在指定天數內
    
    Args:
        article_datetime_str (str): 文章的datetime字符串
        days (int): 天數限制，默認3天
        
    Returns:
        bool: True表示在指定天數內，False表示超過或無法判斷
    """
    if not article_datetime_str or article_datetime_str == "未知時間":
        # 如果沒有時間信息，保險起見返回True（允許抓取）
        return True
    
    article_dt = parse_article_datetime(article_datetime_str)
    if not article_dt:
        # 無法解析時間，保險起見返回True
        return True
    
    # 移除時區信息進行比較（簡化處理）
    if article_dt.tzinfo:
        article_dt = article_dt.replace(tzinfo=None)
    
    current_time = datetime.now()
    time_difference = current_time - article_dt
    
    return time_difference.days < days

def get_main_story_links(main_url, category):
    """步驟 1: 從主頁抓取所有主要故事連結"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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
                
                if href:
                    # 處理相對連結
                    if href.startswith("./"):
                        full_link = "https://news.google.com" + href[1:]
                    else:
                        full_link = "https://news.google.com" + href
                    
                    # 檢查是否已存在於Supabase中
                    should_skip, skip_reason, is_old_story = check_story_exists_in_supabase(full_link, category)
                    
                    if should_skip:
                        print(f"⏭️  跳過故事 {i}: [{category}] {title}")
                        print(f"   原因: {skip_reason}")
                        continue
                    
                    print(f"   處理故事 {i}: {href}")
                    print(f"   📋 檢查結果: {skip_reason}")
                    
                    # 為每個故事生成 UUID
                    story_id = str(uuid.uuid4())
                    
                    story_links.append({
                        "index": i,
                        "story_id": story_id,  # 使用 UUID
                        "title": title,
                        "url": full_link,
                        "category": category,  # 新增：將分類資訊加入
                        "is_old_story": is_old_story  # 新增：標記是否為舊故事
                    })
                    
                    print(f"{i}. 📰 [{category}] {title}")
                    print(f"   🆔 故事ID: {story_id}")
                    print(f"   🔗 {full_link}")
                    if is_old_story:
                        print(f"   ⚠️ 舊故事：只會抓取3天內的新聞")
        
        print(f"\n📊 總共收集到 {len(story_links)} 個 {category} 領域需要處理的主要故事連結")
        
    except Exception as e:
        print(f"❌ 抓取主要故事連結時出錯: {e}")
    finally:
        driver.quit()
    
    return story_links

def get_article_links_from_story(story_info):
    """步驟 2: 進入每個故事頁面，找出所有 article 下的文章連結和相關信息"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    article_links = []
    
    try:
        print(f"\n🔍 正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
        print(f"   🆔 故事ID: {story_info['story_id']}")
        if story_info.get('is_old_story', False):
            print(f"   📅 舊故事模式：只抓取3天內的新聞文章")
        
        driver.get(story_info['url'])
        time.sleep(random.randint(3, 6))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 找到所有 article tag class="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc"
        article_elements = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
        
        print(f"   ✅ 找到 {len(article_elements)} 個 article 元素")
        
        filtered_count = 0
        processed_count = 0
        
        for j, article in enumerate(article_elements, start=1):
            if processed_count >= 20:
                break  # 最多只抓取 20 篇文章

            # 在 article 下面找 h4 tag class="ipQwMb ekueJc RD0gLb"
            h4_element = article.find("h4", class_="ipQwMb ekueJc RD0gLb")
            
            if h4_element:
                # 在 h4 下面找 a tag class="DY5T1d RZIKme"
                link = h4_element.find("a", class_="DY5T1d RZIKme")
                
                if link:
                    href = link.get("href")
                    link_text = link.text.strip()
                    
                    # 找媒體來源 a tag class="wEwyrc"
                    media_element = article.find("a", class_="wEwyrc")
                    media = media_element.text.strip() if media_element else "未知來源"

                    if media == "MSN":
                        continue

                    # 找時間 class="WW6dff uQIVzc Sksgp slhocf"
                    time_element = article.find(class_="WW6dff uQIVzc Sksgp slhocf")
                    article_datetime = time_element.get("datetime") if time_element and time_element.get("datetime") else "未知時間"
                    
                    # 如果是舊故事，檢查文章是否在3天內
                    if story_info.get('is_old_story', False):
                        if not is_article_within_days(article_datetime, days=3):
                            filtered_count += 1
                            print(f"     {j}. ⏭️ 跳過舊文章: {link_text}")
                            print(f"        📅 發布時間: {article_datetime}")
                            continue
                    
                    if href:
                        # 處理相對連結
                        if href.startswith("./"):
                            full_href = "https://news.google.com" + href[1:]
                        else:
                            full_href = "https://news.google.com" + href
                        
                        article_links.append({
                            "story_id": story_info['story_id'],  # 使用 story_id 而非 story_index
                            "story_title": story_info['title'],
                            "story_category": story_info['category'],  # 故事分類
                            "story_url": story_info['url'],
                            "article_index": processed_count + 1,  # 使用處理計數器
                            "article_title": link_text,
                            "article_url": full_href,
                            "media": media,  # 媒體來源
                            "article_datetime": article_datetime,  # 新增：保存文章時間
                        })
                        
                        processed_count += 1
                        print(f"     {processed_count}. 📄 {link_text}")
                        print(f"        🏢 媒體: {media}")
                        print(f"        📅 時間: {article_datetime}")
                        print(f"        🔗 {full_href}")
                    else:
                        print(f"     {j}. ❌ h4 元素中沒有找到對應的 a tag")
                else:
                    print(f"     {j}. ❌ h4 元素中沒有找到對應的 a tag")
            else:
                print(f"     {j}. ❌ article 元素中沒有找到 h4 tag")
        
        if story_info.get('is_old_story', False) and filtered_count > 0:
            print(f"   📊 舊故事過濾統計: 跳過 {filtered_count} 篇超過3天的文章，處理 {processed_count} 篇3天內文章")
        
    except Exception as e:
        print(f"❌ 處理故事時出錯: {e}")
    finally:
        driver.quit()
    
    return article_links

def get_final_content(article_info, driver):
    """步驟 3: 跳轉到原始網站並抓取內容、圖片和時間"""

    MAX_RETRIES = 2
    TIMEOUT = 15
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   嘗試第 {attempt + 1} 次訪問...")
            
            # 設置页面加载超時
            driver.set_page_load_timeout(TIMEOUT)
            
            # 使用 try-except 处理页面加载超时
            try:
                driver.refresh()
                print(f"   刷新頁面: {article_info['article_url']}")
                driver.get(article_info['article_url'])
            except TimeoutException:
                driver.refresh()
                print(f"   ⚠️ 頁面加載超時，但繼續嘗試獲取內容...")
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                    time.sleep(TIMEOUT//2)
                    continue
                else:
                    return None
            
            # 即使超时，也尝试获取已加载的内容
            except WebDriverException as e:
                driver.refresh()
                print(f"   ❌ WebDriver 錯誤: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                    time.sleep(TIMEOUT//2)
                    continue
                else:
                    return None
            
            # 等待一小段時間讓頁面渲染
            time.sleep(random.randint(4, 6))
            
            # 取得跳轉後的真實網址
            try:
                # 檢查是否為需要跳過的 URL
                skip_patterns = [
                    "https://www.gamereactor.cn/video",
                    "https://wantrich.chinatimes.com",
                    "https://taongafarm.site", 
                    "https://www.cmoney.tw",
                    "https://www.cw.com.tw",
                    "https://www.msn.com/",
                    "https://cn.wsj.com/",
                    "https://about.pts.org.tw/pr/latestnews",
                    "https://www.chinatimes.com",
                    "https://newtalk.tw",
                    "https://sports.ltn.com.tw",
                    "https://video.ltn.com.tw",
                    "https://def.ltn.com.tw",
                    "https://www.upmedia.mg",
                    "http://www.aastocks.com",
                    "https://news.futunn.com",
                    "https://ec.ltn.com.tw/",
                    "https://health.ltn.com.tw",
                    "https://www.taiwannews",
                    "https://www.ftvnews.com.tw",
                    "https://tw.nextapple.com",
                    "https://talk.ltn.com.tw",
                    "https://www.mobile01.com/"
                ]
                final_url = driver.current_url
                print(f"   最終網址: {final_url}")
                if(final_url.startswith("https://www.google.com/sorry/index?continue=https://news.google.com/read")):
                    driver.refresh()
                    time.sleep(random.randint(2, 4))
                    final_url = driver.current_url
                elif any(final_url.startswith(pattern) for pattern in skip_patterns):
                    print(f"   ⏭️  跳過連結: {final_url}")
                    return None
                
            except WebDriverException:
                print(f"   ⚠️ 無法獲取當前 URL，使用原始 URL")
                final_url = article_info['article_url']
                return None
            
            # 取得 HTML 原始碼並交給 BeautifulSoup
            try:
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
            except WebDriverException:
                print(f"   ❌ 無法獲取頁面源碼")
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                    time.sleep(TIMEOUT//2)
                    continue
                else:
                    return None

            # 清理內容
            content_to_clean = None

            # 第一優先：尋找 article 標籤
            article_tag = soup.find('article')
            if article_tag and article_info['media'] != 'Now 新聞':
                content_to_clean = str(article_tag)
            elif soup.find('artical'):
                article_tag = soup.find('artical')
                content_to_clean = str(article_tag)
            else:
                # 第二優先：尋找特定 id 的 div 標籤
                target_ids = [
                    'text ivu-mt', 'content-box', 'text', 'boxTitle', 
                    'news-detail-content', 'story', 'article-content__editor', 'article-body', 
                    'artical-content', 'article_text', 'newsText'
                ]
                
                div_by_id = None
                for target_id in target_ids:
                    div_by_id = soup.find('div', id=target_id)
                    if div_by_id:
                        break
                
                if div_by_id:
                    content_to_clean = str(div_by_id)
                else:
                    # 第三優先：尋找特定 class 的 div 標籤
                    target_classes = ['text boxTitle','text ivu-mt', 'paragraph', 'atoms', 
                                      'news-box-text border', 'newsLeading', 'text']

                    div_by_class = None
                    for target_class in target_classes:
                        div_by_class = soup.find('div', class_=target_class)
                        if div_by_class:
                            break
                    
                    if div_by_class:
                        content_to_clean = str(div_by_class)
                    else:
                        # 如果都找不到，使用 body
                        if soup.body:
                            content_to_clean = str(soup.body)

            # 如果有找到內容，進行清理
            if content_to_clean:
                # 重新解析找到的內容
                content_soup = BeautifulSoup(content_to_clean, "html.parser")
                
                # 排除特定的 div 標籤
                excluded_divs = content_soup.find_all('div', class_='paragraph moreArticle')
                for div in excluded_divs:
                    div.decompose()
                
                # 排除特定的 p 標籤
                excluded_p_classes = [
                    'mb-module-gap read-more-vendor break-words leading-[1.4] text-px20 lg:text-px18 lg:leading-[1.8] text-batcave __web-inspector-hide-shortcut__',
                    'mb-module-gap read-more-editor break-words leading-[1.4] text-px20 lg:text-px18 lg:leading-[1.8] text-batcave'
                ]
                
                for p_class in excluded_p_classes:
                    excluded_ps = content_soup.find_all('p', class_=p_class)
                    for p in excluded_ps:
                        p.decompose()
                
                # 最終清理
                body_content = str(content_soup)
                body_content = body_content.replace("\x00", "").replace("\r", "").replace("\n", "")
                body_content = body_content.replace('"', '\\"')
            else:
                body_content = ""
                print(f"   ⚠️ 未找到可用的內容")
                
            # 生成文章 ID
            article_id = str(uuid.uuid4())

            if("您的網路已遭到停止訪問本網站的權利。" in body_content or "我們的系統偵測到您的電腦網路送出的流量有異常情況。" in body_content):
                print(f"   ⚠️ 文章 {article_id} 被封鎖，無法訪問")
                return None

            return {
                "story_id": article_info['story_id'],  # 使用 story_id 而非 story_index
                "story_title": article_info['story_title'],
                "story_category": article_info['story_category'],  # 新增：保存分類
                "story_url": article_info['story_url'],
                "id": article_id,
                "article_index": article_info['article_index'],
                "article_title": article_info['article_title'],
                "google_news_url": article_info['article_url'],
                "final_url": final_url,
                "media": article_info.get('media', '未知來源'),  # 添加媒體來源
                "content": body_content,
            }
            
        except Exception as e:
            print(f"   ❌ 第 {attempt + 1} 次嘗試失敗: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                time.sleep(TIMEOUT//2)
            else:
                print(f"   💀 已達到最大重試次數，放棄該文章")
    
    return None

def create_robust_driver():
    """創建一個更穩健的 WebDriver"""
    # Chrome options 設定
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--page-load-strategy=eager")

    # 用戶代理
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # 防止被識別為自動化
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 廣告和追蹤阻擋
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")

    # 圖片和媒體優化
    chrome_options.add_argument("--disable-background-media")
    chrome_options.add_argument("--disable-background-downloads")
    chrome_options.add_argument("--aggressive-cache-discard")
    chrome_options.add_argument("--disable-sync")

    # 網路優化
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")

    # 記憶體和效能優化
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--no-zygote")

    # 阻擋特定內容類型
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,  # 阻擋通知
            "plugins": 2,        # 阻擋插件
            "popups": 2,         # 阻擋彈出窗口
            "geolocation": 2,    # 阻擋位置請求
            "media_stream": 2,   # 阻擋攝像頭/麥克風
        },
        "profile.managed_default_content_settings": {
            "images": 2,         # 1=允許, 2=阻擋圖片
        },
        "profile.default_content_settings": {
            "popups": 2
        }
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ 創建 WebDriver 失敗: {e}")
        raise

# def save_to_supabase(grouped_articles):
#     """將抓取的新聞數據保存到Supabase"""
#     if not supabase:
#         print("⚠️ Supabase未設定，跳過數據上傳")
#         return
    
#     try:
#         print("💾 正在將數據上傳到Supabase...")
        
#         # 假設您有兩個表：'news_stories' 和 'news_articles'
#         for story in grouped_articles:
#             # 上傳故事記錄
#             story_data = {
#                 'story_id': story['story_id'],
#                 'story_title': story['story_title'],
#                 'story_url': story['story_url'],
#                 'category': story['category'],
#                 'crawl_date': story['crawl_date']
#             }
            
#             # 檢查故事是否已存在，如果存在則更新，否則插入
#             existing_story = supabase.table('stories').select('*').eq('story_id', story['story_id']).execute()
            
#             if existing_story.data:
#                 # 更新現有記錄
#                 supabase.table('stories').update(story_data).eq('story_id', story['story_id']).execute()
#                 print(f"✅ 更新故事: {story['story_title']}")
#             else:
#                 # 插入新記錄
#                 supabase.table('stories').insert(story_data).execute()
#                 print(f"✅ 新增故事: {story['story_title']}")
            
#             # 上傳文章記錄
#             for article in story['articles']:
#                 article_data = {
#                     'article_id': article['article_id'],
#                     'story_id': story['story_id'],
#                     'article_title': article['article_title'],
#                     'article_url': article['article_url'],
#                     'google_news_url': article['google_news_url'],
#                     'media': article['media'],
#                     'content': article['content'],
#                     'crawl_date': story['crawl_date']
#                 }
                
#                 # 檢查文章是否已存在
#                 existing_article = supabase.table('news_articles').select('*').eq('article_id', article['article_id']).execute()
                
#                 if existing_article.data:
#                     # 更新現有記錄
#                     supabase.table('news_articles').update(article_data).eq('article_id', article['article_id']).execute()
#                 else:
#                     # 插入新記錄
#                     supabase.table('news_articles').insert(article_data).execute()
        
#         print("✅ 所有數據已成功上傳到Supabase")
        
#     except Exception as e:
#         print(f"❌ 上傳到Supabase時發生錯誤: {e}")

def main():
    """主執行函式"""
    # 定義要爬取的新聞領域
    topic_sources = [
        {
            "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFZ4ZERBU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
            "category": "Politics"
        },
        {
            "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFptTXpJU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
            "category": "Taiwan News"
        },
        # {
        #     "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "International News"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Science & Technology"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSkwyMHZNREUwWkhONEVnVjZhQzFVVnlnQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Lifestyle & Consumer"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Sports"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Entertainment"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Business & Finance"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "Health & Wellness"
        # }
    ]
    
    # 建立必要的資料夾
    os.makedirs("json", exist_ok=True)
    
    all_article_links = []
    skip_stats = defaultdict(int)  # 統計跳過的故事數量
    
    # === 步驟 1 & 2: 遍歷所有主題領域 ===
    print("=== 開始爬取多個新聞領域 ===")
    
    for topic in topic_sources:
        main_url = topic["url"]
        category = topic["category"]
        
        print(f"\n=== 處理主題：{category} ===")
        
        # 步驟 1: 找到該領域的主要故事連結（已包含Supabase重複檢查）
        story_links = get_main_story_links(main_url, category)
        
        if not story_links:
            print(f"❌ 沒有找到 {category} 領域需要處理的主要故事連結")
            continue
        
        # 步驟 2: 從每個故事抓取文章連結
        print(f"\n=== 從 {category} 領域的每個故事抓取文章連結 ===")
        
        for story in story_links[:8]:  # 可視需求修改數量
            article_links = get_article_links_from_story(story)
            all_article_links.extend(article_links)
            time.sleep(2)
    
    if not all_article_links:
        print("❌ 沒有找到任何需要處理的文章連結")
        return
    
    # === 步驟 3: 抓取文章內容和圖片 ===
    print("\n=== 步驟 3: 抓取文章內容和圖片 ===")
    final_articles = []

    # 創建更穩健的 driver
    try:
        driver = create_robust_driver()
        
        # 先訪問 Google News 主頁
        driver.get("https://news.google.com/")
        time.sleep(2)

        # 匯入 cookies（如果存在）
        try:
            with open("cookies.json", "r", encoding="utf-8") as f:
                cookies = json.load(f)
            for cookie in cookies:
                if 'sameSite' in cookie:
                    cookie.pop('sameSite')
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ 無法添加 cookie: {e}")
        except FileNotFoundError:
            print("⚠️  cookies.json 檔案不存在，繼續執行...")

        # 處理文章
        successful_count = 0
        failed_count = 0
        
        for i, article in enumerate(all_article_links, start=1):  
            print(f"\n處理文章 {i}/{len(all_article_links)} (成功: {successful_count}, 失敗: {failed_count})")
            print(f"   [{article.get('story_category', '未知')}] {article['article_title']}")
            
            content = get_final_content(article, driver)
            
            if content and content.get('content'):
                final_articles.append(content)
                successful_count += 1
                print(f"✅ 成功抓取: [{content['story_category']}] {content['article_title']}")
            else:
                failed_count += 1
                print(f"❌ 無法取得內容")
                
            # 適當的延遲，避免被封
            time.sleep(random.randint(2, 4))

    except Exception as e:
        print(f"❌ WebDriver 初始化或運行失敗: {e}")
        return
    finally:
        try:
            driver.quit()
            print("🔧 WebDriver 已安全關閉")
        except:
            pass

    if not final_articles:
        print("❌ 沒有成功抓取到任何文章內容")
        return

    print(f"\n📊 抓取統計: 成功 {successful_count} 篇, 失敗 {failed_count} 篇")

    # === 依分類和 story_id 分組 ===
    category_grouped = defaultdict(lambda: defaultdict(list))

    for item in final_articles:
        category = item["story_category"]
        story_id = item["story_id"]
        
        category_grouped[category][story_id].append({
            "article_id": item["id"],
            "article_title": item["article_title"],
            "article_index": item["article_index"],
            "google_news_url": item["google_news_url"],
            "article_url": item["final_url"],
            "media": item["media"],
            "content": item["content"],
        })

    # === 為每個分類建立分組文章並儲存 JSON ===
    all_grouped_articles = []
    category_stats = defaultdict(int)
    
    for category, stories in category_grouped.items():
        category_articles = []
        
        for story_id, articles in stories.items():
            # 從 final_articles 中找到對應的故事資訊
            sample_article = next((x for x in final_articles if x["story_id"] == story_id), None)
            if sample_article:
                story_url = sample_article["story_url"]
            else:
                story_url = ""

            # 將文章依照 article_index 排序
            articles_sorted = sorted(articles, key=lambda x: x["article_index"])
            
            # 使用第一篇文章的標題作為 story_title
            story_title = articles_sorted[0]["article_title"] if articles_sorted else ""
                
            category_articles.append({
                "story_id": story_id,
                "story_title": story_title,
                "story_url": story_url,
                "crawl_date": dt.datetime.now().strftime("%Y/%m/%d %H:%M"),
                "category": category,
                "articles": articles_sorted
            })
        
        # 也加入總體列表
        all_grouped_articles.extend(category_articles)

    # === 儲存總體 JSON（原本的功能保留） ===
    with open("json/final_news.json", "w", encoding="utf-8") as f:
        json.dump(all_grouped_articles, f, ensure_ascii=False, indent=2)

    # === 上傳到 Supabase ===
    # if supabase:
    #     save_to_supabase(all_grouped_articles)

    # === 統計資訊 ===
    print(f"\n🎉 完成！總共成功抓取 {len(final_articles)} 篇文章")
    print("📊 各領域文章數量統計:")
    for category, count in category_stats.items():
        print(f"   {category}: {count} 篇")
    print("📁 儲存檔案:")
    print("   - json/final_news.json（所有分類合併）")
    for category in category_stats.keys():
        print(f"   - json/final_news_{category}.json（{category} 分類獨立檔案）")

if __name__ == "__main__":
    main()