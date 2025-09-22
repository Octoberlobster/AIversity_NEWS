from fileinput import filename
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
from dateutil import parser
from google import genai
from google.genai import types
import shutil  

# Supabase imports
from supabase import create_client, Client

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")  # 替換為你的 Supabase URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # 替換為你的 Supabase API Key

# 初始化 Supabase 客戶端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("請先設定你的 GEMINI_API_KEY 環境變數。")

try:
    gemini_client = genai.Client()
except Exception as e:
    raise ValueError(f"無法初始化 Gemini Client，請檢查 API 金鑰：{e}")

def clean_data(data):
    for i, article in enumerate(data):
            print(f"➡️ 正在處理第 {i+1} 篇文章...")
            if "articles" in article:
                for j, sub_article in enumerate(article["articles"]):
                    print(f"   ➡️ 正在處理第 {j+1} 篇子文章...")

                    # (1) 去除 HTML
                    raw_content = sub_article.get("content", "")
                    soup = BeautifulSoup(raw_content, "html.parser")
                    cleaned_text = soup.get_text(separator="\n", strip=True)
                    print(cleaned_text)

                    # (2) 使用 Gemini API 去除雜訊
                    prompt = f"""
                    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                    {cleaned_text}

                    你只需要回覆經過處理的內容，不需要任何其他說明或標題。
                    如果沒有文章內容，請回覆 "[清洗失敗]"。
                    """
                    
                    max_retries = 3  # 設定最大重試次數
                    retries = 0
                    success = False
                    
                    while not success and retries < max_retries:
                        try:
                            # 統一使用 client 的 generate_content 方法
                            response = gemini_client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=prompt
                            )
                            # 獲取回覆內容的方式
                            sub_article["content"] = response.candidates[0].content.parts[0].text.strip()
                            success = True  # 請求成功，跳出迴圈
                            time.sleep(1) # 成功後還是禮貌性地稍等一下
                        except Exception as e:
                            if "503 UNAVAILABLE" in str(e):
                                retries += 1
                                print(f"⚠️ 偵測到模型過載，正在嘗試第 {retries} 次重試...")
                                time.sleep(3 * retries) # 每次重試等待更久
                            else:
                                print(f"❌ 發生錯誤於文章：{filename}，錯誤訊息：{e}")
                                sub_article["content"] = "[清洗失敗]"
                                break # 其他錯誤直接跳出
                    
                    if not success:
                        print(f"❌ 嘗試 {max_retries} 次後仍無法成功處理文章：{filename}")
                        sub_article["content"] = "[清洗失敗]"

    return data

def create_robust_driver(headless: bool = False):
    """創建一個更穩健的 WebDriver"""
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")  # 無頭模式
    else:
        # 有視窗 → 不要加 headless
        options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--page-load-strategy=eager")

    # 用戶代理
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # 防止被識別為自動化
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # 廣告和追蹤阻擋
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")

    # 圖片和媒體優化
    options.add_argument("--disable-background-media")
    options.add_argument("--disable-background-downloads")
    options.add_argument("--aggressive-cache-discard")
    options.add_argument("--disable-sync")

    # 網路優化
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    # 記憶體和效能優化
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    options.add_argument("--single-process")
    options.add_argument("--no-zygote")

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
    options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ 創建 WebDriver 失敗: {e}")
        raise

def get_main_story_links(main_url, category):
    """步驟 1: 從主頁抓取所有主要故事連結"""
    driver = None
    story_links = []
    
    try:
        driver = create_robust_driver(headless=True)
        print(f"🔍 正在抓取 {category} 領域的主要故事連結...")
        driver.get(main_url)
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'c-wiz[jsrenderer="jeGyVb"]')))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        c_wiz_blocks = soup.find_all("c-wiz", {"jsrenderer": "jeGyVb"})
        
        print(f"✅ 找到 {len(c_wiz_blocks)} 個 c-wiz 區塊")
        
        for i, block in enumerate(c_wiz_blocks, start=1):
            try:
                story_link = block.find("a", class_="jKHa4e")
                
                if story_link:
                    href = story_link.get("href")
                    title = story_link.text.strip()
                    
                    if href:
                        if href.startswith("./"):
                            full_link = "https://news.google.com" + href[1:]
                        else:
                            full_link = "https://news.google.com" + href
                        
                        # 檢查資料庫
                        should_skip, action_type, story_data, skip_reason = check_story_exists_in_supabase(
                            full_link, category, "", ""
                        )
                        
                        print(f"   處理故事 {i}: {href}")
                        print(f"   📋 檢查結果: {skip_reason}")
                        
                        # 根據action_type決定story_id
                        if action_type == "add_to_existing_story" and story_data:
                            story_id = story_data["story_id"]
                        else:
                            story_id = str(uuid.uuid4())
                        
                        story_links.append({
                            "index": i,
                            "story_id": story_id,
                            "title": title,
                            "url": full_link,
                            "category": category,
                            "action_type": action_type,
                            "existing_story_data": story_data
                        })
                        
                        print(f"{i}. 📰 [{category}] {title}")
                        print(f"   🆔 故事ID: {story_id}")
                        print(f"   🔗 {full_link}")
                        print(f"   🎯 處理類型: {action_type}")
                        
            except Exception as e:
                print(f"❌ 處理故事區塊 {i} 時出錯: {e}")
                continue
        
        print(f"\n📊 總共收集到 {len(story_links)} 個 {category} 領域需要處理的主要故事連結")
        
    except TimeoutException:
        print(f"❌ 頁面載入超時: {main_url}")
    except WebDriverException as e:
        print(f"❌ WebDriver 錯誤: {e}")
    except Exception as e:
        print(f"❌ 抓取主要故事連結時出錯: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return story_links

def get_article_links_from_story(story_info):
    """
    步驟 2: 進入每個故事頁面，找出所有 article 下的文章連結和相關信息
    增加日期過濾功能
    """
    driver = None
    article_links = []
    
    try:
        driver = create_robust_driver(headless=True)
        print(f"\n🔍 正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
        print(f"   🆔 故事ID: {story_info['story_id']}")
        
        # 取得現有故事的 crawl_date (如果有的話)
        existing_story_data = story_info.get('existing_story_data')
        cutoff_date = None
        if existing_story_data and existing_story_data.get('crawl_date'):
            try:
                cutoff_date_str = existing_story_data['crawl_date']
                if isinstance(cutoff_date_str, str):
                    try:
                        cutoff_date = parser.parse(cutoff_date_str)
                    except:
                        cutoff_date = datetime.strptime(cutoff_date_str, "%Y/%m/%d %H:%M")
                print(f"   📅 只處理 {cutoff_date_str} 之後的文章")
            except Exception as e:
                print(f"   ⚠️ 解析 cutoff_date 時出錯: {e}")
        
        driver.get(story_info['url'])
        time.sleep(random.randint(3, 6))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        article_elements = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
        
        print(f"   ✅ 找到 {len(article_elements)} 個 article 元素")
        
        processed_count = 0
        
        for j, article in enumerate(article_elements, start=1):
            try:
                if processed_count >= 10 :
                    break
                
                h4_element = article.find("h4", class_="ipQwMb ekueJc RD0gLb")
                
                if h4_element:
                    link = h4_element.find("a", class_="DY5T1d RZIKme")
                    
                    if link:
                        href = link.get("href")
                        link_text = link.text.strip()
                        
                        media_element = article.find("a", class_="wEwyrc")
                        media = media_element.text.strip() if media_element else "未知來源"

                        # 跳過特定媒體
                        if media in ["MSN", "自由時報", "chinatimes.com", "中時電子報", 
                                     "中時新聞網", "上報Up Media", "點新聞", "香港文匯網", 
                                     "天下雜誌", "自由健康網", "知新聞", "SUPERMOTO8", 
                                     "警政時報", "大紀元", "新唐人電視台", "arch-web.com.tw",
                                     "韓聯社", "公視新聞網PNN", "優分析UAnalyze", "AASTOCKS.com",
                                     "KSD 韓星網", "商周", "自由財經", "鉅亨號",
                                     "wownews.tw", "utravel.com.hk", "更生新聞網", "香港電台",
                                     "citytimes.tw"]:
                            continue

                        time_element = article.find(class_="WW6dff uQIVzc Sksgp slhocf")
                        article_datetime = "未知時間"
                        
                        if time_element and time_element.get("datetime"):
                            dt_str = time_element.get("datetime")
                            dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                            article_datetime_obj = dt_obj + timedelta(hours=8)
                            article_datetime = article_datetime_obj.strftime("%Y/%m/%d %H:%M:%S")
                            
                            # **重要：檢查文章時間是否在 cutoff_date 之後**
                            if cutoff_date and article_datetime_obj <= cutoff_date:
                                print(f"     ⏭️  跳過舊文章: {link_text}")
                                print(f"        文章時間: {article_datetime} <= 截止時間: {cutoff_date}")
                                continue
                        
                        if href:
                            if href.startswith("./"):
                                full_href = "https://news.google.com" + href[1:]
                            else:
                                full_href = "https://news.google.com" + href
                            
                            # 檢查文章是否需要處理
                            should_skip, action_type, story_data, skip_reason = check_story_exists_in_supabase(
                                story_info['url'], story_info['category'], article_datetime, full_href
                            )
                            
                            if should_skip and action_type == "skip":
                                print(f"     ⏭️  跳過文章: {link_text}")
                                print(f"        原因: {skip_reason}")
                                continue
                            
                            article_links.append({
                                "story_id": story_info['story_id'],
                                "story_title": story_info['title'],
                                "story_category": story_info['category'],
                                "story_url": story_info['url'],
                                "article_index": processed_count + 1,
                                "article_title": link_text,
                                "article_url": full_href,
                                "media": media,
                                "article_datetime": article_datetime,
                                "action_type": action_type,
                                "existing_story_data": story_data
                            })
                            
                            processed_count += 1
                            print(f"     {processed_count}. 📄 {link_text}")
                            print(f"        🏢 媒體: {media}")
                            print(f"        📅 時間: {article_datetime}")
                            print(f"        🎯 處理類型: {action_type}")
                            print(f"        🔗 {full_href}")
                            
            except Exception as e:
                print(f"     ❌ 處理文章元素 {j} 時出錯: {e}")
                continue
        
        if processed_count == 0 and cutoff_date:
            print(f"   ℹ️  此故事沒有 {cutoff_date} 之後的新文章")
        
    except Exception as e:
        print(f"❌ 處理故事時出錯: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return article_links

def get_final_content(article_info, driver):
    """
    步驟 3: 跳轉到原始網站並抓取內容 - 改進錯誤處理
    """
    MAX_RETRIES = 2
    TIMEOUT = 15
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   嘗試第 {attempt + 1} 次訪問...")
            
            # 檢查 driver 是否仍然可用
            try:
                driver.set_page_load_timeout(TIMEOUT)
            except Exception as e:
                print(f"   ❌ WebDriver 設置超時失敗: {e}")
                return None
            
            try:
                driver.get(article_info['article_url'])
            except TimeoutException:
                print(f"   ⚠️ 頁面加載超時，但繼續嘗試獲取內容...")
            except WebDriverException as e:
                print(f"   ❌ WebDriver 錯誤: {e}")
                if "chrome not reachable" in str(e).lower() or "session deleted" in str(e).lower():
                    print(f"   💀 WebDriver 會話已失效")
                    return None
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 {TIMEOUT//4} 秒後重試...")
                    time.sleep(TIMEOUT//4)
                    continue
                else:
                    return None
            except Exception as e:
                print(f"   ❌ 未知錯誤: {e}")
                return None
            
            time.sleep(random.randint(3, 6))
            
            try:
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
                    "https://www.mobile01.com/",
                    "https://www.worldjournal.com/"
                ]
                
                try:
                    final_url = driver.current_url
                    print(f"   最終網址: {final_url}")
                except Exception as e:
                    print(f"   ⚠️ 無法獲取當前 URL: {e}")
                    final_url = article_info['article_url']
                
                if final_url.startswith("https://www.google.com/sorry/index?continue=https://news.google.com/read"):
                    print(f"   ⚠️ 遇到 Google 驗證頁面，嘗試刷新...")
                    try:
                        driver.refresh()
                        time.sleep(random.randint(2, 4))
                        final_url = driver.current_url
                    except:
                        print(f"   ❌ 刷新失敗")
                        return None
                        
                elif any(final_url.startswith(pattern) for pattern in skip_patterns):
                    print(f"   ⏭️  跳過連結: {final_url}")
                    return None
                
            except WebDriverException as e:
                print(f"   ❌ 獲取 URL 時出錯: {e}")
                if "chrome not reachable" in str(e).lower():
                    return None
                final_url = article_info['article_url']
            
            try:
                html = driver.page_source
                if not html or len(html) < 100:  # 檢查頁面內容是否有效
                    print(f"   ⚠️ 頁面內容過短或為空")
                    if attempt < MAX_RETRIES - 1:
                        continue
                    else:
                        return None
                        
                soup = BeautifulSoup(html, "html.parser")
            except WebDriverException as e:
                print(f"   ❌ 無法獲取頁面源碼: {e}")
                if "chrome not reachable" in str(e).lower():
                    return None
                if attempt < MAX_RETRIES - 1:
                    print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                    time.sleep(TIMEOUT//2)
                    continue
                else:
                    return None
            except Exception as e:
                print(f"   ❌ 解析頁面時出錯: {e}")
                return None

            # 內容提取邏輯（保持原有邏輯）
            content_to_clean = None
            article_tag = soup.find('article')
            if article_tag and article_info['media'] != 'Now 新聞':
                content_to_clean = str(article_tag)
            elif soup.find('artical'):
                article_tag = soup.find('artical')
                content_to_clean = str(article_tag)
            else:
                target_ids = [
                    'text ivu-mt', 'content-box', 'text', 'boxTitle', 
                    'news-detail-content', 'story', 'article-content__editor', 'article-body', 
                    'artical-content', 'article_text', 'newsText'
                ]
                
                div_by_id = None
                for target_id in target_ids:
                    try:
                        div_by_id = soup.find('div', id=target_id)
                        if div_by_id:
                            break
                    except Exception as e:
                        continue
                
                if div_by_id:
                    content_to_clean = str(div_by_id)
                else:
                    target_classes = ['articleBody clearfix', 'text boxTitle','text ivu-mt', 'paragraph', 'atoms', 
                                      'news-box-text border', 'newsLeading', 'text']

                    div_by_class = None
                    for target_class in target_classes:
                        try:
                            div_by_class = soup.find('div', class_=target_class)
                            if div_by_class:
                                break
                        except Exception as e:
                            continue
                    
                    if div_by_class:
                        content_to_clean = str(div_by_class)
                    else:
                        if soup.body:
                            content_to_clean = str(soup.body)

            if content_to_clean:
                try:
                    content_soup = BeautifulSoup(content_to_clean, "html.parser")
                    
                    excluded_divs = content_soup.find_all('div', class_='paragraph moreArticle')
                    for div in excluded_divs:
                        div.decompose()
                    
                    excluded_p_classes = [
                        'mb-module-gap read-more-vendor break-words leading-[1.4] text-px20 lg:text-px18 lg:leading-[1.8] text-batcave __web-inspector-hide-shortcut__',
                        'mb-module-gap read-more-editor break-words leading-[1.4] text-px20 lg:text-px18 lg:leading-[1.8] text-batcave'
                    ]
                    
                    for p_class in excluded_p_classes:
                        excluded_ps = content_soup.find_all('p', class_=p_class)
                        for p in excluded_ps:
                            p.decompose()
                    
                    body_content = str(content_soup)
                    body_content = body_content.replace("\x00", "").replace("\r", "").replace("\n", "")
                    body_content = body_content.replace('"', '\\"')
                    
                except Exception as e:
                    print(f"   ❌ 內容清理時出錯: {e}")
                    body_content = ""
            else:
                body_content = ""
                print(f"   ⚠️ 未找到可用的內容")
                
            article_id = str(uuid.uuid4())

            if ("您的網路已遭到停止訪問本網站的權利。" in body_content or 
                "我們的系統偵測到您的電腦網路送出的流量有異常情況。" in body_content):
                print(f"   ⚠️ 文章 {article_id} 被封鎖，無法訪問")
                return None

            return {
                "story_id": article_info['story_id'],
                "story_title": article_info['story_title'],
                "story_category": article_info['story_category'],
                "story_url": article_info['story_url'],
                "id": article_id,
                "article_index": article_info['article_index'],
                "article_title": article_info['article_title'],
                "google_news_url": article_info['article_url'],
                "final_url": final_url,
                "media": article_info.get('media', '未知來源'),
                "content": body_content,
                "article_datetime": article_info.get('article_datetime', '未知時間'),
                "action_type": article_info.get('action_type', 'process'),
                "existing_story_data": article_info.get('existing_story_data')
            }
            
        except Exception as e:
            print(f"   ❌ 第 {attempt + 1} 次嘗試失敗: {e}")
            if "chrome not reachable" in str(e).lower():
                print(f"   💀 Chrome 瀏覽器無法連接，返回 None")
                return None
            if attempt < MAX_RETRIES - 1:
                print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                time.sleep(TIMEOUT//2)
            else:
                print(f"   💀 已達到最大重試次數，放棄該文章")
    
    return None

def check_story_exists_in_supabase(story_url, category, article_datetime="", article_url=""):
    """
    檢查故事是否存在於數據庫中，並返回相應的處理邏輯
    
    Args:
        story_url: 故事URL
        category: 新聞分類
        article_datetime: 文章時間
        article_url: 文章URL
    
    Returns:
        tuple: (should_skip, action_type, story_data, skip_reason)
    """
    try:
        # 1. 檢查 story_url 是否存在，按 crawl_date 降序排列取最新的
        story_response = supabase.table("stories").select("*").eq("story_url", story_url).order("crawl_date", desc=True).limit(1).execute()

        if not story_response.data:
            # 故事不存在，需要創建新故事
            return False, "create_new_story", None, "新故事"
        
        existing_story = story_response.data[0]
        story_id = existing_story["story_id"]
        existing_crawl_date = existing_story["crawl_date"]
        
        # 2. 檢查時間範圍（3天內）
        try:
            if existing_crawl_date:
                # 處理不同的日期格式
                if isinstance(existing_crawl_date, str):
                    try:
                        existing_dt = parser.parse(existing_crawl_date)
                    except:
                        existing_dt = datetime.strptime(existing_crawl_date, "%Y/%m/%d %H:%M")
                else:
                    existing_dt = existing_crawl_date
                    
                current_dt = datetime.now()
                days_diff = (current_dt - existing_dt).days
                
                if days_diff <= 3:
                    # 在3天內，使用現有故事ID
                    print(f"   🔄 使用現有故事ID: {story_id} (距離上次爬取 {days_diff} 天)")
                    print(f"   📅 上次爬取時間: {existing_crawl_date}")
                    
                    # 3. 檢查文章是否在 crawl_date 之後
                    if article_datetime and article_datetime != "未知時間":
                        try:
                            article_dt = parser.parse(article_datetime)
                            
                            # 比較文章時間和上次爬取時間
                            if article_dt <= existing_dt:
                                # 文章時間早於或等於上次爬取時間，跳過
                                return True, "skip", existing_story, f"文章時間 {article_datetime} 早於上次爬取時間 {existing_crawl_date}"
                                
                        except Exception as date_parse_error:
                            print(f"   ⚠️ 文章時間解析錯誤: {date_parse_error}")
                            # 如果無法解析文章時間，繼續檢查 URL
                    
                    # 4. 檢查文章URL是否已存在
                    if article_url:
                        article_response = supabase.table("cleaned_news").select("article_id").eq("article_url", article_url).execute()
                        
                        if article_response.data:
                            # 文章已存在，跳過
                            return True, "skip", existing_story, f"文章已存在於故事 {story_id}"
                        else:
                            # 文章不存在且時間符合，加入現有故事
                            return False, "add_to_existing_story", existing_story, f"加入現有故事 {story_id} (新文章)"
                    else:
                        # 沒有文章URL（故事層級的檢查）
                        return False, "add_to_existing_story", existing_story, f"使用現有故事 {story_id}"
                else:
                    # 超過3天，創建新故事
                    return False, "create_new_story", None, f"超過時間限制 ({days_diff} 天)，創建新故事"
            else:
                # 沒有 crawl_date，創建新故事
                return False, "create_new_story", None, "缺少爬取日期，創建新故事"
                
        except Exception as date_error:
            print(f"   ⚠️ 日期解析錯誤: {date_error}")
            return False, "create_new_story", None, f"日期解析錯誤: {date_error}"
            
    except Exception as e:
        print(f"   ❌ 檢查Supabase時出錯: {e}")
        return False, "create_new_story", None, f"資料庫檢查錯誤: {e}"


def save_story_to_supabase(story_data):
    """
    保存故事到 Supabase stories 表
    """
    try:
        story_record = {
            "story_id": story_data["story_id"],
            "story_url": story_data["story_url"],
            "story_title": story_data["story_title"],
            "category": story_data["category"],
            "crawl_date": story_data["crawl_date"]
        }
        
        # 使用 upsert 來避免重複插入
        response = supabase.table("stories").upsert(story_record, on_conflict="story_id").execute()
        print(f"   ✅ 故事已保存到資料庫: {story_data['story_id']}")
        return True
        
    except Exception as e:
        print(f"   ❌ 保存故事到資料庫失敗: {e}")
        return False

def save_article_to_supabase(article_data, story_id):
    """
    保存文章到 Supabase cleaned_news 表
    """
    try:
        article_record = {
            "article_id": article_data["article_id"],
            "article_title": article_data["article_title"],
            "article_url": article_data["article_url"],
            "content": article_data["content"],
            "media": article_data["media"],
            "story_id": story_id
            }
            
        # 使用 upsert 來避免重複插入
        article_url = article_data["article_url"]
        existing_article = supabase.table("cleaned_news").select("article_id").eq("article_url", article_url).execute()
        if existing_article.data:
            print(f"   ⚠️ 文章已存在，跳過保存: {article_data['article_id']}")
            return True
        elif not article_data["content"] or "[清洗失敗]" in article_data["content"] or "請提供" in article_data["content"]:
            print(f"   ⚠️ 文章內容無效，跳過保存: {article_data['article_id']}")
            return True
        response = supabase.table("cleaned_news").upsert(article_record, on_conflict="article_id").execute()
        print(f"   ✅ 文章已保存到資料庫: {article_data['article_id']}")
        return True
        
    except Exception as e:
        print(f"   ❌ 保存文章到資料庫失敗: {e}")
        return False

def group_articles_by_story_and_time(processed_articles, time_window_days=3):
    """
    根據故事分組，然後在每個故事內按時間將文章分組
    同時支援現有故事的更新功能
    
    Args:
        processed_articles: 從 get_final_content 處理後的文章列表
        time_window_days: 時間窗口天數（真正的每N天分組）
        enable_time_grouping: 是否啟用時間分組功能
    
    Returns:
        list: 處理後的故事列表，包含 action_type 欄位
    """
    print(f"\n=== 開始基於故事和時間分組文章 ===")
    print(f"時間窗口: {time_window_days}天")
    
    # 按故事ID分組
    story_grouped = defaultdict(list)
    for article in processed_articles:
        story_id = article["story_id"]
        story_grouped[story_id].append(article)
    
    all_final_stories = []
    
    for story_id, articles in story_grouped.items():
        if not articles:
            continue
            
        # 獲取故事基本信息（從第一篇文章）
        first_article = articles[0]
        story_title = first_article["article_title"]
        story_url = first_article["story_url"]
        story_category = first_article["story_category"]
        
        # 檢查是否為現有故事更新
        existing_story_data = first_article.get("existing_story_data")
        is_existing_story = existing_story_data and first_article.get("action_type") == "add_to_existing_story"
        
        if is_existing_story:
            print(f"\n🔄 更新現有故事: {story_title}")
            print(f"   🆔 Story ID: {story_id}")
            print(f"   📅 原有 Crawl Date: {existing_story_data.get('crawl_date', '未知')}")
            print(f"   📅 原有時間範圍: {existing_story_data.get('time_range', '未知')}")
            base_action_type = "update_existing_story"
        else:
            print(f"\n🆕 處理新故事: {story_title}")
            print(f"   🆔 Story ID: {story_id}")
            base_action_type = "create_new_story"
        
        print(f"   📊 包含 {len(articles)} 篇文章")
        
        # 解析所有文章的時間
        articles_with_time = []
        for article in articles:
            article_datetime = article.get('article_datetime', '未知時間')
            if article_datetime and article_datetime != '未知時間':
                try:
                    parsed_dt = parser.parse(article_datetime)
                    articles_with_time.append({
                        'article': article,
                        'datetime': parsed_dt
                    })
                except (ValueError, TypeError) as e:
                    print(f"⚠️ 解析時間失敗: {article_datetime}, 使用當前時間")
                    articles_with_time.append({
                        'article': article,
                        'datetime': datetime.now()
                    })
            else:
                # 沒有時間的文章使用當前時間
                articles_with_time.append({
                    'article': article,
                    'datetime': datetime.now()
                })
        
        # 按時間排序
        articles_with_time.sort(key=lambda x: x['datetime'])
        
        # 執行時間窗口分組
        time_groups = _create_time_groups(articles_with_time, time_window_days)
        print(f"   📊 在故事內分成 {len(time_groups)} 個時間組")

        # 為每個時間組創建最終的故事數據
        for group_idx, group in enumerate(time_groups):
            # 找到組內最早和最晚的時間
            earliest_time = min(item['datetime'] for item in group)
            latest_time = max(item['datetime'] for item in group)
            
            # 決定使用哪個時間作為 crawl_date
            if is_existing_story:
                # 現有故事：優先使用原有的 crawl_date，如果沒有則使用當前時間
                original_crawl_date = existing_story_data.get('crawl_date')
                if original_crawl_date:
                    crawl_date = original_crawl_date
                    print(f"      📅 保持原有 Crawl Date: {crawl_date}")
                else:
                    crawl_date = datetime.now().strftime("%Y/%m/%d %H:%M")
                    print(f"      📅 使用當前時間作為 Crawl Date: {crawl_date}")
            else:
                # 新故事：使用最早文章時間
                crawl_date = earliest_time.strftime("%Y/%m/%d %H:%M")
            
            # 計算實際的時間範圍 - 對於現有故事，優先使用原有時間範圍
            if is_existing_story and existing_story_data.get('time_range'):
                # 現有故事且有時間範圍：合併新舊時間範圍
                original_time_range = existing_story_data.get('time_range')
                try:
                    # 解析原有時間範圍
                    if ' - ' in original_time_range:
                        orig_start_str, orig_end_str = original_time_range.split(' - ')
                        orig_start = datetime.strptime(orig_start_str, '%Y/%m/%d')
                        orig_end = datetime.strptime(orig_end_str, '%Y/%m/%d')
                    else:
                        orig_start = orig_end = datetime.strptime(original_time_range, '%Y/%m/%d')
                    
                    # 計算合併後的時間範圍
                    combined_start = min(orig_start, earliest_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    combined_end = max(orig_end, latest_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    
                    if combined_start.date() == combined_end.date():
                        time_range = combined_start.strftime('%Y/%m/%d')
                    else:
                        time_range = f"{combined_start.strftime('%Y/%m/%d')} - {combined_end.strftime('%Y/%m/%d')}"
                    
                    print(f"      📅 合併時間範圍: {original_time_range} + {earliest_time.strftime('%Y/%m/%d')}~{latest_time.strftime('%Y/%m/%d')} = {time_range}")
                    
                except (ValueError, TypeError) as e:
                    print(f"      ⚠️ 解析原有時間範圍失敗: {original_time_range}，使用新文章時間範圍")
                    # 如果解析失敗，使用新文章的時間範圍
                    if earliest_time.date() == latest_time.date():
                        time_range = earliest_time.strftime('%Y/%m/%d')
                    else:
                        time_range = f"{earliest_time.strftime('%Y/%m/%d')} - {latest_time.strftime('%Y/%m/%d')}"
            else:
                # 新故事或現有故事沒有時間範圍：使用新文章的時間範圍
                if earliest_time.date() == latest_time.date():
                    time_range = earliest_time.strftime('%Y/%m/%d')
                else:
                    time_range = f"{earliest_time.strftime('%Y/%m/%d')} - {latest_time.strftime('%Y/%m/%d')}"
            
            # 生成最終的故事ID和標題
            if len(time_groups) > 1:
                # 多個時間組：需要為每組生成新的ID
                if is_existing_story:
                    # 現有故事分組：保持原ID並添加組別後綴
                    base_story_id = story_id
                    final_story_id = f"{base_story_id}_G{group_idx + 1:02d}"
                    final_action_type = f"{base_action_type}_with_time_grouping"
                else:
                    # 新故事分組：標準的分組邏輯
                    base_story_id = story_id[:-2] if len(story_id) >= 2 else story_id
                    final_story_id = f"{base_story_id}{group_idx + 1:02d}"
                    final_action_type = f"{base_action_type}_with_time_grouping"
                
                final_story_title = f"{story_title} (第{group_idx + 1}組)"
            else:
                # 單一組：保持原有ID和標題
                final_story_id = story_id
                final_story_title = story_title
                final_action_type = base_action_type
            
            # 準備文章列表
            grouped_articles = []
            for article_idx, item in enumerate(group, 1):
                article = item['article']
                grouped_articles.append({
                    "article_id": article["id"],
                    "article_title": article["article_title"],
                    "article_index": article_idx,  # 重新編號
                    "google_news_url": article["google_news_url"],
                    "article_url": article["final_url"],
                    "media": article["media"],
                    "content": article["content"],
                    "original_datetime": article.get("article_datetime", "未知時間")
                })
            
            # 創建故事數據結構
            story_data = {
                "story_id": final_story_id,
                "story_title": final_story_title,
                "story_url": story_url,
                "crawl_date": crawl_date,
                "time_range": time_range,
                "category": story_category,
                "articles": grouped_articles,
                "action_type": final_action_type,
                "is_time_grouped": len(time_groups) > 1,
                "group_index": group_idx + 1 if len(time_groups) > 1 else None,
                "total_groups": len(time_groups) if len(time_groups) > 1 else None
            }
            
            # 如果是現有故事，保留更多原有數據的參考
            if is_existing_story:
                story_data["original_story_data"] = existing_story_data
                story_data["time_range_updated"] = existing_story_data.get('time_range') != time_range
                story_data["crawl_date_preserved"] = existing_story_data.get('crawl_date') == crawl_date
            
            all_final_stories.append(story_data)
            
            # 計算實際天數跨度
            actual_days = (latest_time.date() - earliest_time.date()).days + 1
            
            if len(time_groups) > 1:
                print(f"   📰 時間組 {group_idx + 1}: {time_range} (實際跨度: {actual_days}天)")
            else:
                print(f"   📰 完整故事: {time_range} (實際跨度: {actual_days}天)")
            
            print(f"      🆔 最終 Story ID: {final_story_id}")
            print(f"      📅 Crawl Date: {crawl_date}")
            print(f"      📄 文章數: {len(grouped_articles)} 篇")
            print(f"      🎯 處理類型: {final_action_type}")
    
    print(f"\n✅ 總共處理完成 {len(all_final_stories)} 個最終故事")
    return all_final_stories


def _create_time_groups(articles_with_time, time_window_days):
    """
    根據時間窗口將文章分組的內部函數
    """
    time_groups = []
    current_group = []
    current_group_start_time = None
    current_group_end_time = None
    
    for item in articles_with_time:
        article_time = item['datetime']
        
        if current_group_start_time is None:
            # 第一篇文章，開始第一組
            current_group_start_time = article_time
            current_group_end_time = article_time + timedelta(days=time_window_days)
            current_group.append(item)
            print(f"      🏁 開始新組: {current_group_start_time.strftime('%Y/%m/%d %H:%M')} - {current_group_end_time.strftime('%Y/%m/%d %H:%M')}")
        else:
            # 檢查是否在當前組的時間窗口內
            if article_time < current_group_end_time:
                # 在同一組內
                current_group.append(item)
                print(f"         ✅ 加入當前組: {article_time.strftime('%Y/%m/%d %H:%M')}")
            else:
                # 超出時間窗口，開始新的一組
                if current_group:
                    time_groups.append(current_group)
                    print(f"      📦 完成組別，包含 {len(current_group)} 篇文章")
                
                # 開始新組
                current_group = [item]
                current_group_start_time = article_time
                current_group_end_time = article_time + timedelta(days=time_window_days)
                print(f"      🏁 開始新組: {current_group_start_time.strftime('%Y/%m/%d %H:%M')} - {current_group_end_time.strftime('%Y/%m/%d %H:%M')}")
    
    # 添加最後一組
    if current_group:
        time_groups.append(current_group)
        print(f"      📦 完成最後組別，包含 {len(current_group)} 篇文章")
    
    return time_groups


def save_stories_to_supabase(stories):
    """
    批量保存故事和文章到Supabase數據庫
    """
    try:
        saved_stories = 0
        updated_stories = 0
        saved_articles = 0
        
        for story in stories:
            story_id = story["story_id"]
            action_type = story.get("action_type", "create_new_story")
            
            # 根據 action_type 決定如何處理故事
            if action_type.startswith("create_new_story"):
                # 保存新故事
                if save_story_to_supabase(story):
                    saved_stories += 1
            elif action_type.startswith("update_existing_story"):
                # 更新現有故事的 crawl_date
                try:
                    update_data = {
                        "crawl_date": story["crawl_date"]
                    }
                    # response = supabase.table("stories").update(update_data).eq("story_id", story_id).execute()
                    print(f"   ✅ 故事 crawl_date 已更新: {story_id}")
                    updated_stories += 1
                except Exception as e:
                    print(f"   ❌ 更新故事 crawl_date 失敗: {e}")
            
            # 保存文章（無論是新故事還是現有故事）
            for article in story["articles"]:
                if save_article_to_supabase(article, story_id):
                    saved_articles += 1
        
        print(f"✅ 批量保存完成: {saved_stories} 個新故事, {updated_stories} 個更新故事, {saved_articles} 篇文章")
        return True
        
    except Exception as e:
        print(f"❌ 批量保存到Supabase時出錯: {e}")
        return False

def process_news_pipeline(main_url, category):
    """
    完整的新聞處理管道 - 改進的 WebDriver 管理
    """
    print(f"🚀 開始處理 {category} 分類的新聞...")
    
    # 步驟1: 獲取所有故事連結
    story_links = get_main_story_links(main_url, category)
    if not story_links:
        print("❌ 沒有找到任何故事連結")
        return []
    
    # 步驟2: 處理每個故事，獲取所有文章連結
    all_article_links = []
    for story_info in story_links[:10]:
        article_links = get_article_links_from_story(story_info)
        all_article_links.extend(article_links)
    
    if not all_article_links:
        print("❌ 沒有找到任何文章連結")
        return []
    
    print(f"\n📊 總共收集到 {len(all_article_links)} 篇文章待處理")
    
    # 步驟3: 獲取每篇文章的完整內容 - 改進的錯誤處理
    final_articles = []
    driver = None
    consecutive_failures = 0  # 連續失敗計數
    max_consecutive_failures = 3  # 最大連續失敗次數
    
    def create_fresh_driver():
        """創建新的 driver 實例"""
        try:
            new_driver = create_robust_driver(headless=True)
            initialize_driver_with_cookies(new_driver)
            return new_driver
        except Exception as e:
            print(f"   ❌ 創建新 WebDriver 失敗: {e}")
            return None
    
    # 初始化 driver
    driver = create_fresh_driver()
    if not driver:
        print("❌ 無法創建初始 WebDriver，終止處理")
        return []
    
    try:
        for i, article_info in enumerate(all_article_links, 1):
            print(f"\n🔄 處理文章 {i}/{len(all_article_links)}: {article_info['article_title']}")
            
            # 檢查 driver 是否仍然有效
            try:
                # 簡單的 driver 健康檢查
                current_url = driver.current_url
            except Exception as e:
                print(f"   ⚠️ WebDriver 異常，重新創建: {e}")
                try:
                    driver.quit()
                except:
                    pass
                driver = create_fresh_driver()
                if not driver:
                    print(f"   ❌ 無法重新創建 WebDriver，跳過剩餘 {len(all_article_links) - i + 1} 篇文章")
                    break
            
            article_content = get_final_content(article_info, driver)
            
            if article_content:
                final_articles.append(article_content)
                print(f"   ✅ 成功獲取內容")
                consecutive_failures = 0  # 重置連續失敗計數
                
            else:
                print(f"   ❌ 無法獲取內容")
                consecutive_failures += 1
                
                # 檢查是否需要重新創建 driver
                if consecutive_failures >= max_consecutive_failures:
                    print(f"   🔄 連續 {consecutive_failures} 次失敗，重新創建 WebDriver...")
                    
                    try:
                        driver.quit()
                    except:
                        pass
                    
                    driver = create_fresh_driver()
                    if not driver:
                        print(f"   ❌ 無法重新創建 WebDriver，跳過剩餘 {len(all_article_links) - i + 1} 篇文章")
                        break
                    
                    consecutive_failures = 0  # 重置計數
                    print(f"   ✅ WebDriver 重新創建完成")
                    
                    # 可選：重新嘗試當前文章
                    print(f"   🔄 重新嘗試處理當前文章...")
                    article_content = get_final_content(article_info, driver)
                    if article_content:
                        final_articles.append(article_content)
                        print(f"   ✅ 重新嘗試成功")
                    else:
                        print(f"   ❌ 重新嘗試仍然失敗")
            
            # 隨機延遲
            time.sleep(random.randint(2, 4))
            
    except KeyboardInterrupt:
        print(f"\n⚡ 用戶中斷處理")
        
    except Exception as e:
        print(f"\n💥 處理過程中發生嚴重錯誤: {e}")
        import traceback
        print(f"📋 錯誤詳情:\n{traceback.format_exc()}")
        
    finally:
        if driver:
            try:
                print(f"\n🔧 清理 WebDriver 資源...")
                driver.quit()
                print(f"   ✅ WebDriver 清理完成")
            except Exception as e:
                print(f"   ⚠️ WebDriver 清理時出現問題: {e}")
    
    print(f"\n📊 文章內容獲取完成: 成功 {len(final_articles)}/{len(all_article_links)} 篇")
    
    # 步驟4: 按故事和時間分組
    final_stories = group_articles_by_story_and_time(final_articles, time_window_days=3)
    
    return final_stories

def initialize_driver_with_cookies(driver):
    """初始化 WebDriver 並載入 cookies"""
    try:
        # 先訪問 Google News 主頁
        driver.get("https://news.google.com/")
        time.sleep(2)
        
        # 嘗試載入 cookies
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
            
            print("✅ Cookies 載入完成")
            
        except FileNotFoundError:
            print("⚠️ cookies.json 檔案不存在，使用默認設置")
    
    except Exception as e:
        print(f"⚠️ 初始化 WebDriver cookies 時出錯: {e}")

def save_stories_to_json(stories, filename):
    """
    將故事數據保存到JSON文件
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stories, f, ensure_ascii=False, indent=2)
        print(f"✅ 數據已保存到 {filename}")
        return True
    except Exception as e:
        print(f"❌ 保存文件時出錯: {e}")
        return False



def main():
    """
    主函數 - 新聞爬蟲的入口點
    """
    print("="*80)
    print("🌟 Google News 爬蟲程序啟動")
    print("="*80)
    
    # 配置需要處理的新聞分類
    news_categories = {
        "Politics": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFZ4ZERBU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Taiwan News": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFptTXpJU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "International News": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Science & Technology": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Lifestyle & Consumer": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSkwyMHZNREUwWkhONEVnVjZhQzFVVnlnQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Sports": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Entertainment": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Business & Finance": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        "Health & Wellness": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    }

    
    # 可以選擇處理特定分類或全部分類
    # selected_categories = ["Politics"]#"Science & Technology"]#, "Business & Finance", "Health & Wellness", "Sports", "Entertainment", "Lifestyle & Consumer", ]#"Taiwan News", "International News", "Politics"]# 可以修改這裡來選擇要處理的分類
    selected_categories = list(news_categories.keys())  # 處理所有分類
    
    all_final_stories = []
    start_time = time.time()
    
    try:
        for category in selected_categories:
            if category not in news_categories:
                print(f"⚠️ 未知的分類: {category}")
                continue
                
            category_start_time = time.time()
            print(f"\n{'='*60}")
            print(f"🎯 開始處理分類: {category}")
            print(f"{'='*60}")
            
            # 處理該分類的新聞
            category_stories = process_news_pipeline(news_categories[category], category)
            
            if category_stories:
                all_final_stories.extend(category_stories)
                category_end_time = time.time()
                category_duration = category_end_time - category_start_time
                
                print(f"\n✅ {category} 分類處理完成!")
                print(f"   📊 獲得 {len(category_stories)} 個故事")
                print(f"   ⏱️  耗時: {category_duration:.2f} 秒")
            else:
                print(f"\n❌ {category} 分類處理失敗，沒有獲得任何故事")
            
            # 分類之間的延遲
            if category != selected_categories[-1]:  # 不是最後一個分類
                print(f"\n⏳ 等待 30 秒後處理下一個分類...")
                time.sleep(30)
        
        # 處理完成後的統計
        total_end_time = time.time()
        total_duration = total_end_time - start_time
        
        print(f"\n{'='*80}")
        print(f"🎉 所有分類處理完成!")
        print(f"{'='*80}")
        print(f"📊 最終統計:")
        print(f"   🏷️  處理分類數: {len(selected_categories)}")
        print(f"   📰 總故事數: {len(all_final_stories)}")
        
        # 統計每個分類的故事數
        category_counts = {}
        total_articles = 0
        for story in all_final_stories:
            category = story['category']
            category_counts[category] = category_counts.get(category, 0) + 1
            total_articles += len(story['articles'])
        
        for category, count in category_counts.items():
            print(f"   📂 {category}: {count} 個故事")
        
        print(f"   📄 總文章數: {total_articles}")
        print(f"   ⏱️  總耗時: {total_duration:.2f} 秒 ({total_duration/60:.1f} 分鐘)")
        
        # 保存數據
        if all_final_stories:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            all_final_stories = clean_data(all_final_stories)
            # 保存到JSON文件
            # json_filename = f"json/google_news_stories_{timestamp}.json"
            
            json_filename = f"json/final_news.json"
            if save_stories_to_json(all_final_stories, json_filename):
                print(f"📁 本地JSON文件: {json_filename}")
            
            # 保存到數據庫（如果需要）
            try:
                save_stories_to_supabase(all_final_stories)
                print("💾 數據庫保存: 已跳過 (請根據需要實現)")
            except Exception as e:
                print(f"❌ 數據庫保存失敗: {e}")
            
        else:
            print("⚠️ 沒有獲得任何故事數據")
    
    except KeyboardInterrupt:
        print(f"\n⚡ 程序被用戶中斷")
        if all_final_stories:
            # 即使被中斷，也保存已獲取的數據
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"json/google_news_stories_interrupted_{timestamp}.json"
            save_stories_to_json(all_final_stories, json_filename)
            print(f"📁 已保存中斷前的數據: {json_filename}")
    
    except Exception as e:
        print(f"\n💥 程序執行過程中發生錯誤: {e}")
        import traceback
        print(f"📋 錯誤詳情:\n{traceback.format_exc()}")
    
    finally:
        print(f"\n{'='*80}")
        print(f"👋 Google News 爬蟲程序結束")
        print(f"{'='*80}")

if __name__ == "__main__":
    main()