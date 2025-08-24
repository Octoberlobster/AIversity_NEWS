import json
import time
import random
import uuid
import os
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

def create_robust_driver(headless: bool = False):
    """創建一個更穩健的 WebDriver"""
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")  # 無頭模式
    else:
        # 有視窗 → 不要加 headless
        options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    return driver

def check_story_exists_in_supabase(story_url, category, article_datetime, article_url):
    """检查故事是否存在于数据库中（占位符函数）"""
    # 这里应该是实际的数据库检查逻辑
    # 现在返回默认值，表示处理所有文章
    return False, "process", None, "新文章"

def get_main_story_links(main_url, category):
    """步驟 1: 從主頁抓取所有主要故事連結"""
    driver = None
    story_links = []
    
    try:
        driver = create_robust_driver(headless=True)

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
            try:
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
                        
                        # 检查数据库
                        should_skip, action_type, story_data, skip_reason = check_story_exists_in_supabase(
                            full_link, category, "", ""
                        )
                        
                        print(f"   處理故事 {i}: {href}")
                        print(f"   📋 檢查結果: {skip_reason}")
                        
                        # 為每個故事生成 UUID
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
    """步驟 2: 進入每個故事頁面，找出所有 article 下的文章連結和相關信息"""
    driver = None
    article_links = []
    
    try:
        driver = create_robust_driver(headless=True)

        print(f"\n🔍 正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
        print(f"   🆔 故事ID: {story_info['story_id']}")
        
        driver.get(story_info['url'])
        time.sleep(random.randint(3, 6))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 找到所有 article tag
        article_elements = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
        
        print(f"   ✅ 找到 {len(article_elements)} 個 article 元素")
        
        processed_count = 0
        
        for j, article in enumerate(article_elements, start=1):
            try:
                if processed_count >= 10:
                    break  # 最多只抓取 15 篇文章

                # 在 article 下面找 h4 tag
                h4_element = article.find("h4", class_="ipQwMb ekueJc RD0gLb")
                
                if h4_element:
                    # 在 h4 下面找 a tag
                    link = h4_element.find("a", class_="DY5T1d RZIKme")
                    
                    if link:
                        href = link.get("href")
                        link_text = link.text.strip()
                        
                        # 找媒體來源
                        media_element = article.find("a", class_="wEwyrc")
                        media = media_element.text.strip() if media_element else "未知來源"

                        if media == "MSN" or media == "自由時報" or media == "chinatimes.com" or media == "中時電子報" or media == "中時新聞網" or media == "上報Up Media":
                            continue

                        # 找時間
                        time_element = article.find(class_="WW6dff uQIVzc Sksgp slhocf")
                        if time_element and time_element.get("datetime"):
                            dt_str = time_element.get("datetime")  # e.g. "2025-08-21T07:15:00Z"
                            # 解析成 datetime (假設來源是 UTC 格式，ISO 8601)
                            dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

                            # 加上 8 小時（UTC+8 → 台灣時間）
                            article_datetime = dt_obj + timedelta(hours=8)
                            article_datetime = article_datetime.strftime("%Y-%m-%d %H:%M:%S")

                        else:
                            article_datetime = "未知時間"

                        if href:
                            # 處理相對連結
                            if href.startswith("./"):
                                full_href = "https://news.google.com" + href[1:]
                            else:
                                full_href = "https://news.google.com" + href
                            
                            # 進階檢查：包含文章資訊
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
                        else:
                            print(f"     {j}. ⚠️ 找不到文章連結")
                    else:
                        print(f"     {j}. ⚠️ h4 元素中沒有找到對應的 a tag")
                else:
                    print(f"     {j}. ⚠️ article 元素中沒有找到 h4 tag")
                    
            except Exception as e:
                print(f"     ❌ 處理文章元素 {j} 時出錯: {e}")
                continue
        
    except TimeoutException:
        print(f"❌ 故事頁面載入超時: {story_info['url']}")
    except WebDriverException as e:
        print(f"❌ WebDriver 錯誤: {e}")
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
    """步驟 3: 跳轉到原始網站並抓取內容、圖片和時間"""
    MAX_RETRIES = 2
    TIMEOUT = 15
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   嘗試第 {attempt + 1} 次訪問...")
            
            # 設置页面加载超時
            driver.set_page_load_timeout(TIMEOUT)
            
            # 使用 try-except 处理页面加载超時
            try:
                driver.get(article_info['article_url'])
            except TimeoutException:
                print(f"   ⚠️ 頁面加載超時，但繼續嘗試獲取內容...")
                # 即使超时，也尝试获取已加载的内容
            except WebDriverException as e:
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
                    # "https://newtalk.tw",
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
                final_url = driver.current_url
                print(f"   最終網址: {final_url}")
                
                if final_url.startswith("https://www.google.com/sorry/index?continue=https://news.google.com/read"):
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
                    try:
                        div_by_id = soup.find('div', id=target_id)
                        if div_by_id:
                            break
                    except Exception as e:
                        print(f"   ⚠️ 搜尋 ID '{target_id}' 時出錯: {e}")
                        continue
                
                if div_by_id:
                    content_to_clean = str(div_by_id)
                else:
                    # 第三優先：尋找特定 class 的 div 標籤
                    target_classes = ['articleBody clearfix', 'text boxTitle','text ivu-mt', 'paragraph', 'atoms', 
                                      'news-box-text border', 'newsLeading', 'text']

                    div_by_class = None
                    for target_class in target_classes:
                        try:
                            div_by_class = soup.find('div', class_=target_class)
                            if div_by_class:
                                break
                        except Exception as e:
                            print(f"   ⚠️ 搜尋 class '{target_class}' 時出錯: {e}")
                            continue
                    
                    if div_by_class:
                        content_to_clean = str(div_by_class)
                    else:
                        # 如果都找不到，使用 body
                        if soup.body:
                            content_to_clean = str(soup.body)

            # 如果有找到內容，進行清理
            if content_to_clean:
                try:
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
                    
                except Exception as e:
                    print(f"   ❌ 內容清理時出錯: {e}")
                    body_content = ""
            else:
                body_content = ""
                print(f"   ⚠️ 未找到可用的內容")
                
            # 生成文章 ID
            article_id = str(uuid.uuid4())

            # 檢查是否被封鎖
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
            if attempt < MAX_RETRIES - 1:
                print(f"   🔄 {TIMEOUT//2} 秒後重試...")
                time.sleep(TIMEOUT//2)
            else:
                print(f"   💀 已達到最大重試次數，放棄該文章")
    
    return None


def find_earliest_datetime(articles):
    """找到文章列表中最早的時間"""
    valid_datetimes = []
    
    for article in articles:
        article_datetime = article.get('article_datetime', '未知時間')
        if article_datetime and article_datetime != '未知時間':
            try:
                # 嘗試解析 datetime 字符串
                parsed_dt = parser.parse(article_datetime)
                valid_datetimes.append(parsed_dt)
            except (ValueError, TypeError) as e:
                print(f"⚠️ 解析時間失敗: {article_datetime}, 錯誤: {e}")
                continue
    
    if valid_datetimes:
        # 找到最早的時間並格式化
        earliest_dt = min(valid_datetimes)
        return earliest_dt
    else:
        # 如果沒有有效的時間，使用當前時間
        return datetime.now()


def group_articles_by_story_and_time(processed_articles, time_window_days=2):
    """
    根據故事分組，然後在每個故事內按時間將文章分組
    processed_articles: 從 get_final_content 處理後的文章列表
    time_window_days: 時間窗口天數（真正的每N天分組）
    """
    print(f"\n=== 開始基於故事和時間分組文章（每個故事內按{time_window_days}天分組）===")
    
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
        
        print(f"\n🔍 處理故事: {story_title}")
        print(f"   🆔 Story ID: {story_id}")
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
        
        # 在同一故事內進行時間分組 - 修正的邏輯
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
        
        print(f"   📊 在故事內分成 {len(time_groups)} 個時間組")
        
        # 為每個時間組創建最終的故事數據
        for group_idx, group in enumerate(time_groups):
            # 找到組內最早和最晚的時間
            earliest_time = min(item['datetime'] for item in group)
            latest_time = max(item['datetime'] for item in group)
            
            crawl_date = earliest_time.strftime("%Y/%m/%d %H:%M")
            
            # 計算實際的時間範圍
            if earliest_time.date() == latest_time.date():
                time_range = earliest_time.strftime('%Y/%m/%d')
            else:
                time_range = f"{earliest_time.strftime('%Y/%m/%d')} - {latest_time.strftime('%Y/%m/%d')}"
            
            # 如果一個故事被分成多個時間組，為每組生成新的故事ID
            if len(time_groups) > 1:
                base_story_id = story_id[:-2]  # 移除最後兩碼
                final_story_id = f"{base_story_id}{group_idx + 1:02d}"  # 添加兩位數的組索引
                final_story_title = f"{story_title} (第{group_idx + 1}組)"
            else:
                final_story_id = story_id
                final_story_title = story_title
            
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
            
            story_data = {
                "story_id": final_story_id,
                "story_title": final_story_title,
                "story_url": story_url,
                "crawl_date": crawl_date,
                "time_range": time_range,
                "category": story_category,
                "articles": grouped_articles
            }
            
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
            
            # 驗證時間窗口
            if actual_days > time_window_days:
                print(f"      ⚠️  警告: 實際跨度 ({actual_days}天) 超過設定窗口 ({time_window_days}天)")
    
    print(f"\n✅ 總共處理完成 {len(all_final_stories)} 個最終故事")
    return all_final_stories

def process_news_pipeline(main_url, category):
    """
    完整的新聞處理管道
    """
    print(f"🚀 開始處理 {category} 分類的新聞...")
    
    # 步驟1: 獲取所有故事連結
    story_links = get_main_story_links(main_url, category)
    if not story_links:
        print("❌ 沒有找到任何故事連結")
        return []
    
    # 步驟2: 處理每個故事，獲取所有文章連結
    all_article_links = []
    for story_info in story_links[:4 ]:
        article_links = get_article_links_from_story(story_info)
        all_article_links.extend(article_links)
    
    if not all_article_links:
        print("❌ 沒有找到任何文章連結")
        return []
    
    print(f"\n📊 總共收集到 {len(all_article_links)} 篇文章待處理")
    
    # 步驟3: 獲取每篇文章的完整內容
    final_articles = []
    driver = create_robust_driver(headless=False)  # 使用有視窗模式以便於調試
    
    initialize_driver_with_cookies(driver)
    
    try:
        for i, article_info in enumerate(all_article_links, 1):
            print(f"\n🔄 處理文章 {i}/{len(all_article_links)}: {article_info['article_title']}")
            
            article_content = get_final_content(article_info, driver)
            if article_content:
                final_articles.append(article_content)
                print(f"   ✅ 成功獲取內容")
            else:
                print(f"   ❌ 無法獲取內容")
            
            # 隨機延遲
            time.sleep(random.randint(2, 4))
            
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
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

def save_stories_to_supabase(stories):
    """
    將故事數據保存到Supabase數據庫
    這個函數需要根據你的Supabase配置來實現
    """
    try:
        # 這裡需要實現你的Supabase保存邏輯
        # 例如：
        # for story in stories:
        #     supabase.table('stories').insert(story).execute()
        
        print(f"✅ 已將 {len(stories)} 個故事保存到Supabase")
        return True
    except Exception as e:
        print(f"❌ 保存到Supabase時出錯: {e}")
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
    selected_categories = ["Politics"]#, "Taiwan News", "International News"]  # 可以修改這裡來選擇要處理的分類
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
            
            # 保存到JSON文件
            json_filename = f"json/google_news_stories_{timestamp}.json"
            if save_stories_to_json(all_final_stories, json_filename):
                print(f"📁 本地JSON文件: {json_filename}")
            
            # 保存到數據庫（如果需要）
            try:
                # save_stories_to_supabase(all_final_stories)
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