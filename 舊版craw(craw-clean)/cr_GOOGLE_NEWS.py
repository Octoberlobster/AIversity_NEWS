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
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Chrome options 設定
chrome_options = Options()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

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
                    
                    # 為每個故事生成 UUID
                    story_id = str(uuid.uuid4())
                    
                    story_links.append({
                        "index": i,
                        "story_id": story_id,  # 使用 UUID
                        "title": title,
                        "url": full_link,
                        "category": category  # 新增：將分類資訊加入
                    })
                    
                    print(f"{i}. 📰 [{category}] {title}")
                    print(f"   🆔 故事ID: {story_id}")
                    print(f"   🔗 {full_link}")
        
        print(f"\n📊 總共收集到 {len(story_links)} 個 {category} 領域的主要故事連結")
        
    except Exception as e:
        print(f"❌ 抓取主要故事連結時出錯: {e}")
    finally:
        driver.quit()
    
    return story_links

def get_article_links_from_story(story_info):
    """步驟 2: 進入每個故事頁面，找出所有 article 下的文章連結和相關信息"""
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    article_links = []
    
    try:
        print(f"\n🔍 正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
        print(f"   🆔 故事ID: {story_info['story_id']}")
        driver.get(story_info['url'])
        time.sleep(random.randint(3, 6))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 找到所有 article tag class="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc"
        article_elements = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
        
        print(f"   ✅ 找到 {len(article_elements)} 個 article 元素")
        
        for j, article in enumerate(article_elements, start=1):
            if j > 3:
                break  # 最多只抓取 5 篇文章    
            
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
                    media_source = media_element.text.strip() if media_element else "未知來源"
                    
                    # 找時間 class="WW6dff uQIVzc Sksgp slhocf"
                    time_element = article.find(class_="WW6dff uQIVzc Sksgp slhocf")
                    article_datetime = time_element.get("datetime") if time_element and time_element.get("datetime") else "未知時間"
                    
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
                            "article_index": j,
                            "article_title": link_text,
                            "article_url": full_href,
                            "media_source": media_source,  # 媒體來源
                        })
                        
                        print(f"     {j}. 📄 {link_text}")
                        print(f"        🏢 媒體: {media_source}")
                        print(f"        🔗 {full_href}")
                else:
                    print(f"     {j}. ❌ h4 元素中沒有找到對應的 a tag")
            else:
                print(f"     {j}. ❌ article 元素中沒有找到 h4 tag")
        
    except Exception as e:
        print(f"❌ 處理故事時出錯: {e}")
    finally:
        driver.quit()
    
    return article_links

def get_final_content(article_info, driver):
    """步驟 3: 跳轉到原始網站並抓取內容、圖片和時間"""
    try:
        driver.get(article_info['article_url'])
        time.sleep(random.randint(3, 6))
        
        # 取得跳轉後的真實網址
        final_url = driver.current_url
        print(f"   最終網址: {final_url}")
        
        # 取得 HTML 原始碼並交給 BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # 清理內容
        content_to_clean = None

        # 第一優先：尋找 article 標籤
        article_tag = soup.find('article')
        if article_tag:
            content_to_clean = str(article_tag)
        else:
            # 第二優先：尋找特定 id 的 div 標籤
            target_ids = [
                'content-box', 'text', 'boxTitle', 'news-detail-content', 
                'story', 'article-content__editor', 'article-body', 
                'artical-content', 'article_text'
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
                target_classes = ['paragraph', 'atoms']
                
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
            
        # 生成文章 ID
        article_id = str(uuid.uuid4())
            
        return {
            "story_id": article_info['story_id'],  # 使用 story_id 而非 story_index
            "story_title": article_info['story_title'],
            "story_category": article_info['story_category'],  # 新增：保存分類
            "id": article_id,
            "article_index": article_info['article_index'],
            "article_title": article_info['article_title'],
            "google_news_url": article_info['article_url'],
            "final_url": final_url,
            "media_source": article_info.get('media_source', '未知來源'),  # 添加媒體來源
            "content": body_content,
        }
        
    except Exception as e:
        print(f"     ❌ 無法取得內容: {e}")
    
    return None

def main():
    """主執行函式"""
    # 定義要爬取的新聞領域
    topic_sources = [
        # {
        #     "url": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFZ4ZERBU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "政治"
        # },
        # {
        #     "url": "https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "科學與科技"
        # },
        {
            "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
            "category": "體育"
        },
        # {
        #     "url": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant",
        #     "category": "商業"
        # }
        # 可以繼續添加更多領域...
        # {
        #     "url": "其他 Google News 主題 URL",
        #     "category": "其他領域名稱"
        # }
    ]
    
    # 建立必要的資料夾
    os.makedirs("json", exist_ok=True)
    
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
        
        for story in story_links[:4]:  # 可視需求修改數量
            article_links = get_article_links_from_story(story)
            all_article_links.extend(article_links)
            time.sleep(2)
    
    # 儲存文章連結（非必要，可註解）
    # with open("json/article_links.json", "w", encoding="utf-8") as f:
    #     json.dump(all_article_links, f, ensure_ascii=False, indent=2)
    # print(f"\n✅ 所有文章連結已儲存到 article_links.json (總共 {len(all_article_links)} 個)")

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
    for i, article in enumerate(all_article_links, start=1):  
        print(f"\n處理文章 {i}/{len(all_article_links)}")
        print(f"   [{article.get('story_category', '未知')}] {article['article_title']}")
        
        content = get_final_content(article, driver)
        
        if content:
            final_articles.append(content)
            print(f"✅ 成功抓取: [{content['story_category']}] {content['article_title']}")
        else:
            print(f"❌ 無法取得內容")
            
        time.sleep(1)

    driver.quit()

    if not final_articles:
        print("❌ 沒有成功抓取到任何文章內容")
        return

    # === 依 story_id 分組並使用第一篇文章標題作為 story_title ===
    grouped = defaultdict(list)

    for item in final_articles:
        grouped[item["story_id"]].append({
            "id": item["id"],
            "article_index": item["article_index"],
            "article_title": item["article_title"],
            "google_news_url": item["google_news_url"],
            "final_url": item["final_url"],
            "media_source": item["media_source"],
            "content": item["content"],
        })

    grouped_articles = []
    for story_id in grouped.keys():
        # 從 final_articles 中找到對應的故事資訊
        sample_article = next((x for x in final_articles if x["story_id"] == story_id), None)
        if sample_article:
            story_category = sample_article["story_category"]
        else:
            story_category = "未知"
        
        # 將文章依照 article_index 排序
        articles_sorted = sorted(grouped[story_id], key=lambda x: x["article_index"])
        
        # 使用第一篇文章的標題作為 story_title
        story_title = articles_sorted[0]["article_title"] if articles_sorted else ""
            
        grouped_articles.append({
            "story_id": story_id,  # 使用 story_id 而非 story_index
            "story_title": story_title,  # 使用第一篇文章的標題
            "crawl_date": dt.datetime.now().strftime("%Y/%m/%d %H:%M"),  # 爬取時間
            "category": story_category,  # 新增：分類資訊
            "articles": articles_sorted
        })

    # === 儲存分組 JSON ===
    with open("json/final_news.json", "w", encoding="utf-8") as f:
        json.dump(grouped_articles, f, ensure_ascii=False, indent=2)

    # === 統計資訊 ===
    category_stats = defaultdict(int)
    for article in final_articles:
        category_stats[article['story_category']] += 1

    print(f"\n🎉 完成！總共成功抓取 {len(final_articles)} 篇文章")
    print("📊 各領域文章數量統計:")
    for category, count in category_stats.items():
        print(f"   {category}: {count} 篇")
    print("📁 儲存檔案:")
    print("   - New_Summary/data/final_news.json（依 story_id 分組，包含領域分類）")
    print("   - json/article_links.json（所有文章連結）")

if __name__ == "__main__":
    main()