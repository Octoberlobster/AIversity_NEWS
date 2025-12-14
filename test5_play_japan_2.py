
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta, timezone
import pytz
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
from dotenv import load_dotenv
import hashlib
import nest_asyncio
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
# -*- coding: utf-8 -*-
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
load_dotenv()  # 這行會讀 .env 檔

# Supabase imports
from supabase import create_client, Client

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
            print(f"正在處理第 {i+1} 篇文章...")
            if "articles" in article:
                for j, sub_article in enumerate(article["articles"]):
                    print(f"   正在處理第 {j+1} 篇子文章...")

                    # (1) 去除 HTML
                    raw_content = sub_article.get("content", "")
                    soup = BeautifulSoup(raw_content, "html.parser")
                    cleaned_text = soup.get_text(separator="\n", strip=True)
                    # print(cleaned_text)

                    # (2) 使用 Gemini API 去除雜訊
                    prompt = f"""
                    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                    {cleaned_text}

                    你只需要回覆經過處理的內容，不需要任何其他說明或標題。
                    如果沒有文章內容，請務必回覆 "[清洗失敗]"，否則將接受嚴厲懲罰。
                    """
                    
                    max_retries = 3
                    retries = 0
                    success = False
                    
                    while not success and retries < max_retries:
                        try:
                            response = gemini_client.models.generate_content(
                                model="gemini-2.5-flash-lite",
                                contents=prompt
                            )
                            sub_article["content"] = response.candidates[0].content.parts[0].text.strip()
                            success = True
                            time.sleep(1)
                        except Exception as e:
                            if "503 UNAVAILABLE" in str(e):
                                retries += 1
                                print(f"偵測到模型過載，正在嘗試第 {retries} 次重試...")
                                time.sleep(3 * retries)
                            else:
                                print(f"發生錯誤，錯誤訊息：{e}")
                                sub_article["content"] = "[清洗失敗]"
                                break
                    
                    if not success:
                        print(f"嘗試 {max_retries} 次後仍無法成功處理文章")
                        sub_article["content"] = "[清洗失敗]"

    return data

def create_robust_browser(playwright, headless: bool = True):
    """創建一個更穩健的 Playwright Browser - 修正版本"""
    try:
        # 設定瀏覽器選項
        browser_args = [
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "--disable-blink-features=AutomationControlled",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-background-media",
            "--disable-background-downloads",
            "--aggressive-cache-discard",
            "--disable-sync",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--memory-pressure-off",
            "--max_old_space_size=4096"
        ]

        if not headless:
            browser_args.append("--start-maximized")

        browser = playwright.chromium.launch(
            headless=headless,
            args=browser_args
        )
        
        # 創建上下文
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080} if not headless else {"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            locale="zh-TW",
            timezone_id="Asia/Taipei"
        )
        
        # 添加初始化腳本，防止被偵測為自動化
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-TW', 'zh', 'en'],
            });
        """)
        
        # 阻擋某些資源類型以提升效能
        context.route("**/*", lambda route: (
            route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
            else route.continue_()
        ))
        
        return browser, context
        
    except Exception as e:
        print(f"創建 Playwright Browser 失敗: {e}")
        raise

def get_main_story_links(main_url, country, category):
    """步驟 1: 從主頁抓取所有主要故事連結 - 修正版本"""
    story_links = []
    
    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            browser, context = create_robust_browser(p, headless=True)
            page = context.new_page()
            
            print(f"正在抓取 {category} 領域的主要故事連結...")
            
            # 設定超時時間
            page.set_default_timeout(10000)
            
            page.goto(main_url)
            
            # 等待特定元素載入
            page.wait_for_selector('c-wiz[jsrenderer="jeGyVb"]', timeout=10000)
            
            # 取得頁面內容
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            c_wiz_blocks = soup.find_all("c-wiz", {"jsrenderer": "jeGyVb"})
            
            print(f"找到 {len(c_wiz_blocks)} 個 c-wiz 區塊")
            
            for i, block in enumerate(c_wiz_blocks, start=1):
                if i > 7:
                    break
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

                            full_link = full_link + "&so=1"  # 強制按時間排序
                            print("\n")
                            # 檢查資料庫（包含內容比對）
                            should_skip, action_type, story_data, skip_reason, final_url, final_title = check_story_exists_in_supabase(
                                full_link, category, "", "", title
                            )
                            
                            print(f"   處理故事 {i}: {href}")
                            print(f"   檢查結果: {skip_reason}")
                            
                            # ========== 修改：根據 action_type 決定 story_id ==========
                            if action_type == "add_to_existing_story" and story_data:
                                # 加入現有故事，使用現有 story_id
                                story_id = story_data["story_id"]
                            # elif action_type == "create_new_group" and story_data:
                            #     # 創建新組，生成新的 story_id
                            #     existing_story_id = story_data["story_id"]
                            #     if len(existing_story_id) >= 2 and existing_story_id[-2:].isdigit():
                            #         current_group_num = int(existing_story_id[-2:])
                            #         base_story_id = existing_story_id[:-2]
                            #         next_group_num = current_group_num + 1
                            #         story_id = f"{base_story_id}{next_group_num:02d}"
                            #     else:
                            #         # 如果沒有分組格式，默認創建第二組
                            #         story_id = f"{existing_story_id}02"
                            else:
                                # 創建新故事，生成新的 UUID
                                story_id = str(uuid.uuid4())
                            # ========== 修改結束 ==========
                            
                            story_links.append({
                                "index": i,
                                "story_id": story_id,
                                "title": final_title,  # 使用最終標題
                                "url": final_url,      # 使用最終URL
                                "category": category,
                                "action_type": action_type,
                                "existing_story_data": story_data,
                                "country": country
                            })
                            
                            print(f"{i}. [{category}] {final_title}")
                            print(f"   故事ID: {story_id}")
                            print(f"   {final_url}")
                            print(f"   處理類型: {action_type}")
                            
                except Exception as e:
                    print(f"處理故事區塊 {i} 時出錯: {e}")
                    continue
            
            print(f"\n總共收集到 {len(story_links)} 個 {category} 領域需要處理的主要故事連結")
            
        except PlaywrightTimeoutError:
            print(f"頁面載入超時: {main_url}")
        except Exception as e:
            print(f"抓取主要故事連結時出錯: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
    
    return story_links

def get_article_links_from_story(story_info):
    """步驟 2: 進入每個故事頁面，找出所有 article 下的文章連結和相關信息"""
    article_links = []
    
    with sync_playwright() as p:
        try:
            browser, context = create_robust_browser(p, headless=True)
            page = context.new_page()
            
            print(f"\n正在處理故事 {story_info['index']}: [{story_info['category']}] {story_info['title']}")
            print(f"   故事ID: {story_info['story_id']}")
            
            # 取得現有故事的 crawl_date (如果有的話)
            existing_story_data = story_info.get('existing_story_data')
            cutoff_date = None
            if existing_story_data and existing_story_data.get('crawl_date'):
                try:
                    cutoff_date_str = existing_story_data['crawl_date']
                    if isinstance(cutoff_date_str, str):
                        # 先解析為台北時間
                        taipei_dt = datetime.strptime(cutoff_date_str, "%Y/%m/%d %H:%M")
                        # 設置為台北時區
                        taipei_tz = timezone(timedelta(hours=8))
                        taipei_dt = taipei_dt.replace(tzinfo=taipei_tz)
                        # 轉換為 UTC
                        cutoff_date = taipei_dt.astimezone(taipei_tz)
                    print(f"   只處理 {cutoff_date_str} (UTC+8: {cutoff_date.strftime('%Y/%m/%d %H:%M')}) 之後的文章")
                except Exception as e:
                    print(f"   解析 cutoff_date 時出錯: {e}")
            
            # 轉成 UTC aware
            # if cutoff_date.tzinfo is None:
            #     cutoff_date = cutoff_date.replace(tzinfo=timezone.utc)
            # else:
            #     cutoff_date = cutoff_date.astimezone(timezone.utc)

            page.goto(story_info['url'])
            time.sleep(random.randint(3, 6))
            
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            article_elements = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
            
            print(f"   找到 {len(article_elements)} 個 article 元素")
            
            processed_count = 0
            
            for j, article in enumerate(article_elements, start=1):
                try:
                    if processed_count >= 6:
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
                                         "KSD 韓星網", "商周", "自由財經", "鉅亨號","gamereactor.cn"
                                         "wownews.tw", "utravel.com.hk", "更生新聞網", "香港電台","CIDRAP"
                                         "citytimes.tw", "三立新聞網SETN.com", "聯合新聞網", "RP Online",
                                         "La Provence", "Yahoo!ファイナンス", "Media Indonesia", "CNN Indonesia",
                                         "au Webポータル", "tenki.jp", "FOX Weather", "Houston Chronicle", "NOLA.com",
                                         "WPLG Local 10", "The New York Times", "台灣好報", "CT Insider", "PBS",
                                         "Reuters", "WTOP", "福井新聞社", "大紀元", "台灣達人秀TTshow", "facebook.com",
                                         "壹蘋新聞網", "CMoney", "上毛新聞電子版", "臺灣導報", "Kompas.id", "商周",
                                         "CCTV.com English", "Taiwan News", "RTL.fr", "Investing.com 香港 - 股市報價& 財經新聞",
                                         "Báo điện tử Tiền Phong", "ig.com", "107.9 LITE FM", "BÁO SÀI GÒN GIẢI PHÓNG",
                                        "Haibunda","Investing.com India","dotdotnews","MSNBC News","KTVZ","Euronews.com",
                                        "Báo Nhân Dân điện tử","FXStreet","三菱マテリアル","Fox News","六度世界","forecastock.tw",
                                        "the-independent.com","TBS NEWS DIG","20 Minutes","Daily Tribune","Federal News Network",
                                        "WKMG","CNBC Indonesia","Albert Lea Tribune","Facebook","地球黃金線","4Gamer.net", "MarketWatch",
                                        "The Daily Beast", "美麗島電子報", "經理人", "X", "Newswav", "PressReader", "Men's Journal", 
                                        "The Hill", "ESPN", "The Wall Street Journal", "bola.okezone.com", "台灣新聞雲報", "Ottumwa Courier",
                                        "Washington Times", "San Francisco Examiner", "Toronto Sun", "Investing.com", "Business Insider", "video.okezone.com",
                                        "netralnews.com", "singtao.ca"
                                        ]:
                                continue

                            time_element = article.find(class_="WW6dff uQIVzc Sksgp slhocf")
                            article_datetime = ""
                            
                            if time_element and time_element.get("datetime"):
                                dt_str = time_element.get("datetime")
                                dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                                article_datetime_obj = dt_obj + timedelta(hours=8)
                                article_datetime = article_datetime_obj.strftime("%Y/%m/%d %H:%M")
                                
                                # 檢查文章時間是否在 cutoff_date 之後
                                if cutoff_date and article_datetime_obj <= cutoff_date:
                                    print(f"     跳過舊文章: {link_text}")
                                    print(f"        文章時間: {article_datetime} <= 截止時間: {cutoff_date}")
                                    continue
                            
                            if href:
                                if href.startswith("./"):
                                    full_href = "https://news.google.com" + href[1:]
                                else:
                                    full_href = "https://news.google.com" + href
                                

                                print("story_url" + story_info['url'])

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
                                    "action_type": story_info["action_type"],
                                    "existing_story_data": story_info.get("existing_story_data", None)
                                })
                                
                                processed_count += 1
                                print(f"     {processed_count}. {link_text}")
                                print(f"        媒體: {media}")
                                print(f"        時間: {article_datetime}")
                                # print(f"        處理類型: {action_type}")
                                print(f"        {full_href}")
                                
                except Exception as e:
                    print(f"     處理文章元素 {j} 時出錯: {e}")
                    continue
            
            if processed_count == 0 and cutoff_date:
                print(f"   此故事沒有 {cutoff_date} 之後的新文章")
            
        except Exception as e:
            print(f"處理故事時出錯: {e}")
        finally:
            try:
                browser.close()
            except:
                pass
    
    return article_links

def get_final_content(article_info, page):
    """步驟 3: 跳轉到原始網站並抓取內容 - 使用 Playwright (改善版本)"""
    MAX_RETRIES = 2
    TIMEOUT = 8000  # 縮短為 8秒 (Playwright使用毫秒)

    for attempt in range(MAX_RETRIES):
        try:
            print(f"   尝试第 {attempt + 1} 次访问...")
            
            # 设定页面超时
            page.set_default_timeout(TIMEOUT)
            
            try:
                # 簡化頁面加載，只等待 DOM 加載完成
                page.goto(article_info['article_url'], timeout=TIMEOUT, wait_until='domcontentloaded')
                
                # 簡化等待邏輯，避免過度等待
                try:
                    # 短暫等待網絡空閒，但不強制要求
                    page.wait_for_load_state('networkidle', timeout=3000)
                except PlaywrightTimeoutError:
                    # 網絡空閒超時不是致命錯誤，繼續執行
                    print(f"   网络空闲超时，继续处理...")
                    
            except PlaywrightTimeoutError:
                print(f"   页面加载超时，尝试继续...")
                # 超時後嘗試基本等待
                try:
                    page.wait_for_load_state('domcontentloaded', timeout=2000)
                except:
                    print(f"   基本DOM加载也超时，强制继续...")
            except Exception as e:
                print(f"   页面导航错误: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"   2秒后重试...")
                    time.sleep(2)
                    continue
                else:
                    return None
            
            # 減少隨機等待時間
            time.sleep(random.randint(1, 2))
            
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
                    "https://www.worldjournal.com/",
                    "https://www.cna.com.tw/newsmorningworld",
                    "https://www.yahoo.com/creators/",
                    "https://www.rfi.fr/tw/%E5%B0%88%E6%AC%84%E6%AA%A2%E7%B4%A2",
                    "https://fnc.ebc.net.tw/fncnews",
                    "https://news.ttv.com.tw/Video/",
                    "https://www.wiwo.de/erfolg",
                    "https://today.line.me/tw/v3/posts",
                    "https://www.nbcnews.com/meet-the-press/video/",
                    "https://www.nbcnews.com/video/",
                    "https://www.independent.co.uk/bulletin/news/",
                    "https://www.the-independent.com/bulletin/news/",
                    "https://www.socialnews.xyz/",
                    "https://tw.tv.yahoo.com/",
                    "https://tw.sports.yahoo.com/video/"
                ]
                
                # 簡化URL獲取邏輯
                final_url = article_info['article_url']  # 預設值
                try:
                    current_url = page.url
                    if current_url:
                        final_url = current_url
                        print(f"   最终网址: {final_url}")
                except Exception as e:
                    print(f"   获取URL时出错，使用原始URL: {e}")
                
                if final_url.startswith("https://www.google.com/sorry/index?continue=https://news.google.com/read"):
                    print(f"   遇到 Google 验证页面，跳过...")
                    return None
                        
                elif any(final_url.startswith(pattern) for pattern in skip_patterns):
                    print(f"   跳过连结: {final_url}")
                    return None
                
                elif check_article_exists_in_supabase(final_url):
                    print(f"   文章已存在於 Supabase，跳过: {final_url}")
                    return None
                
            except Exception as e:
                print(f"   URL处理异常: {e}")
                final_url = article_info['article_url']
            
            try:
                # 改善頁面內容獲取邏輯，避免卡死
                print(f"   获取页面内容...")
                
                html = None
                max_content_attempts = 2
                
                for attempt_num in range(max_content_attempts):
                    try:
                        # 先檢查頁面狀態
                        try:
                            # 設定較短超時專門給 evaluate 使用
                            page.set_default_timeout(5000)  # 5秒超時
                            page_title = page.evaluate("document.title") or ""
                            print(f"   页面标题: {page_title[:50]}...")
                        except Exception:
                            print(f"   无法获取页面标题...")
                        
                        # 方法1: 使用 page.evaluate() 獲取 HTML (推薦)
                        print(f"   使用 evaluate() 获取HTML... (第 {attempt_num + 1} 次)")
                        
                        html = page.evaluate("""
                            () => {
                                // 確保頁面已載入
                                if (document.readyState !== 'complete' && document.readyState !== 'interactive') {
                                    return null;
                                }
                                // 獲取完整的 HTML
                                return document.documentElement.outerHTML;
                            }
                        """)
                        
                        # 恢復原本超時設定
                        page.set_default_timeout(TIMEOUT)
                        
                        if html and len(html) > 100:
                            print(f"   evaluate() 成功获取内容，长度: {len(html)}")
                            break
                        else:
                            print(f"   evaluate() 内容过短或为空，尝试其他方法...")
                            
                            # 方法2: 回退到 page.content()
                            try:
                                print(f"   回退使用 page.content()...")
                                page.set_default_timeout(3000)  # 3秒超時
                                html = page.content()
                                page.set_default_timeout(TIMEOUT)
                                
                                if html and len(html) > 100:
                                    print(f"   page.content() 获取成功，长度: {len(html)}")
                                    break
                            except PlaywrightTimeoutError:
                                print(f"   page.content() 超时")
                                page.set_default_timeout(TIMEOUT)
                            
                            # 方法3: 使用 evaluate() 獲取 body 內容
                            try:
                                print(f"   尝试获取 body 内容...")
                                page.set_default_timeout(3000)
                                body_html = page.evaluate("document.body ? document.body.outerHTML : ''")
                                page.set_default_timeout(TIMEOUT)
                                
                                if body_html and len(body_html) > 100:
                                    html = f"<html><head></head>{body_html}</html>"
                                    print(f"   body 内容获取成功，长度: {len(html)}")
                                    break
                            except Exception as e:
                                print(f"   获取 body 失败: {e}")
                                page.set_default_timeout(TIMEOUT)
                            
                            time.sleep(1)
                            
                    except PlaywrightTimeoutError:
                        print(f"   evaluate() 超时，尝试下一种方法...")
                        page.set_default_timeout(TIMEOUT)
                        continue
                        
                    except Exception as error:
                        print(f"   获取内容时出错: {error}")
                        page.set_default_timeout(TIMEOUT)
                        
                        error_msg = str(error).lower()
                        if "navigating" in error_msg or "loading" in error_msg:
                            print(f"   页面仍在加载，等待...")
                            time.sleep(1)
                        elif "timeout" in error_msg:
                            print(f"   超时错误，跳过...")
                            break
                        else:
                            time.sleep(0.5)
                    
                    # 最後檢查
                    if attempt_num == max_content_attempts - 1 and not html:
                        print(f"   所有方法都失败，最后检查页面状态...")
                        try:
                            url_check = page.url
                            ready_state = page.evaluate("document.readyState")
                            print(f"   页面状态 - URL: {url_check[:50]}..., readyState: {ready_state}")
                        except Exception:
                            print(f"   页面已无响应...")
                            break
                
                # 檢查最終結果
                if not html or len(html) < 100:
                    print(f"   页面内容获取失败或内容过短 (最终长度: {len(html) if html else 0})")
                    if attempt < MAX_RETRIES - 1:
                        continue
                    else:
                        return None
                
                # 解析HTML
                print(f"   开始解析HTML...")
                soup = BeautifulSoup(html, "html.parser")
                
            except Exception as e:
                print(f"   页面内容处理时出错: {e}")
                if attempt < MAX_RETRIES - 1:
                    print(f"   1秒后重试...")
                    time.sleep(1)
                    continue
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
                    print(f"   内容清理时出错: {e}")
                    body_content = ""
            else:
                body_content = ""
                print(f"   未找到可用的内容")
                return None
                
            article_id = str(uuid.uuid4())

            if ("您的網路已遭到停止訪問本網站的權利。" in body_content or 
                "我們的系統偵測到您的電腦網路送出的流量有異常情況。" in body_content):
                print(f"   文章 {article_id} 被封锁，无法访问")
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
                "media": article_info.get('media', '未知来源'),
                "content": body_content,
                "article_datetime": article_info.get('article_datetime', ''),

                # 待處理欄位
                "action_type": article_info.get('action_type', 'create_new_story'),
                "existing_story_data": article_info.get('existing_story_data')
            }
            
        except Exception as e:
            print(f"   第 {attempt + 1} 次尝试失败: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"   2秒后重试...")
                time.sleep(2)
            else:
                print(f"   已达到最大重试次数，放弃该文章")
    
    return None

def check_story_exists_in_supabase(story_url, category, article_datetime="", article_url="", title=""):
    """
    检查故事是否存在于数据库中，并返回相应的处理逻辑
    
    Args:
        story_url: 故事URL
        category: 新闻分类
        article_datetime: 文章时间
        article_url: 文章URL
        title: 故事標題
    
    Returns:
        tuple: (should_skip, action_type, story_data, skip_reason, final_url, final_title)
    """
    try:
        # 1. 先檢查完整 story_url 是否存在
        story_response = supabase.table("stories").select("*").eq("story_url", story_url).order("crawl_date", desc=True).limit(1).execute()

        # 2. 如果完整URL不存在，檢查前88個字符是否匹配
        if not story_response.data:
            url_prefix = story_url[:88]
            # 使用 LIKE 查詢前88個字符相同的記錄
            prefix_response = supabase.table("stories").select("*").like("story_url", f"{url_prefix}%").order("crawl_date", desc=True).execute()
            
            if prefix_response.data:
                print(f"   找到前88字符匹配的故事，開始內容比對...")
                
                # 使用 get_hash 比較內容
                for existing_story in prefix_response.data:
                    existing_url = existing_story["story_url"]
                    try:
                        # 比較兩個URL的內容hash
                        new_hash, new_text = get_hash_smart_env(story_url)  # 改為同步版本
                        existing_hash, existing_text = get_hash_smart_env(existing_url)  # 改為同步版本

                        if new_hash == existing_hash or new_text == existing_text:
                            print(f"   內容相同！沿用舊連結: {existing_url}")
                            print(f"   沿用舊標題: {existing_story.get('story_title', title)}")
                            
                            # 使用舊的URL和標題，但繼續原本的時間檢查邏輯
                            return check_existing_story_logic(
                                existing_story, 
                                article_datetime, 
                                article_url, 
                                existing_url,  # 使用舊URL
                                existing_story.get('story_title', title)  # 使用舊標題
                            )
                    except Exception as hash_error:
                        print(f"   內容比對失敗: {hash_error}")
                        continue
                
                print(f"   前88字符匹配但內容不同，創建新故事")
        
        if not story_response.data:
            # 故事不存在，需要创建新故事
            return False, "create_new_story", None, "新故事", story_url, title
        
        existing_story = story_response.data[0]
        existing_url = existing_story["story_url"]
        return check_existing_story_logic(existing_story, article_datetime, article_url, existing_url, title)
            
    except Exception as e:
        print(f"   检查Supabase时出错: {e}")
        return False, "create_new_story", None, f"数据库检查错误: {e}", story_url, title


def check_existing_story_logic(existing_story, article_datetime, article_url, final_url, final_title):
    """
    檢查現有故事的處理邏輯
    """
    story_id = existing_story["story_id"]
    existing_crawl_date = existing_story["crawl_date"]
    
    # 2. 检查时间范围（3天内）
    try:
        if existing_crawl_date:
            # 处理不同的日期格式
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
                # 在3天内，使用现有故事ID
                print(f"   使用现有故事ID: {story_id} (距离上次爬取 {days_diff} 天)")
                print(f"   上次爬取时间: {existing_crawl_date}")
                
                # ========== 新增：檢查尾數並創建新組 ==========
                # 檢查 story_id 是否以 0X 結尾（X 為 1-4，分組標識）
                # if len(story_id) >= 2 and story_id[-2] == '0' and story_id[-1] in '1234':
                #     current_group_num = int(story_id[-1])  # 取得最後一位數字 (1-4)
                #     base_story_id = story_id[:-2]
                    
                #     # 檢查是否需要創建新組
                #     if current_group_num > 0:  # 01, 02, 03, 04
                #         next_group_num = current_group_num + 1
                #         if next_group_num <= 8:  # 確保不超過 04
                #             new_story_id = f"{base_story_id}0{next_group_num}"
                #         else:
                #             # 如果超過 04，可以根據需求處理（例如回到 01 或報錯）
                #             new_story_id = f"{base_story_id}10"  # 循環回 01
                        
                #         print(f"   檢測到分組故事，當前為第 {current_group_num} 組")
                        
                #         # 返回創建新組的標記
                #         return False, "create_new_group", existing_story, f"創建新組 (第{next_group_num}組)", final_url, final_title
                # ========== 新增邏輯結束 ==========
                
                # 3. 检查文章是否在 crawl_date 之后
                if article_datetime and article_datetime != "未知时间":
                    try:
                        article_dt = parser.parse(article_datetime)
                        
                        # 比较文章时间和上次爬取时间
                        if article_dt <= existing_dt:
                            # 文章时间早于或等于上次爬取时间，跳过
                            return True, "skip", existing_story, f"文章时间 {article_datetime} 早于上次爬取时间 {existing_crawl_date}", final_url, final_title
                            
                    except Exception as date_parse_error:
                        print(f"   文章时间解析错误: {date_parse_error}")
                        # 如果无法解析文章时间，继续检查 URL
                
                # 4. 检查文章URL是否已存在
                if article_url:
                    article_response = supabase.table("cleaned_news").select("article_id").eq("article_url", article_url).execute()
                    
                    if article_response.data:
                        # 文章已存在，跳过
                        return True, "skip", existing_story, f"文章已存在於故事 {story_id}", final_url, final_title
                    else:
                        # 文章不存在且时间符合，加入现有故事
                        return False, "add_to_existing_story", existing_story, f"加入现有故事 {story_id} (新文章)", final_url, final_title
                else:
                    # 没有文章URL（故事层级的检查）
                    return False, "add_to_existing_story", existing_story, f"使用现有故事 {story_id}", final_url, final_title
            else:
                # 超过3天，创建新故事
                return False, "create_new_story", None, f"超过时间限制 ({days_diff} 天)，创建新故事", final_url, final_title
        else:
            # 没有 crawl_date，创建新故事
            return False, "create_new_story", None, "缺少爬取日期，创建新故事", final_url, final_title
            
    except Exception as date_error:
        print(f"   日期解析错误: {date_error}")
        return False, "create_new_story", None, f"日期解析错误: {date_error}", final_url, final_title

# 方案1: 使用線程池執行同步代碼
def get_hash_sync_threaded(url):
    """
    在線程池中執行同步 Playwright 代碼 (強化版)
    功能：
    1. 阻擋圖片載入 (加速)
    2. 清洗 HTML 雜訊 (Header, Footer, Script, Ads)
    3. 正規化文字 (去除標點與大小寫差異)
    4. 提取 Google News 特定標題作為 link_text
    """
    def _get_hash_in_thread():
        browser = None
        context = None
        page = None
        try:
            with sync_playwright() as p:
                # 創建瀏覽器 (假設 create_robust_browser 已定義)
                # 如果沒有定義，請將其替換為 p.chromium.launch(headless=True)
                browser, context = create_robust_browser(p, headless=True)
                page = context.new_page()
                
                # [優化 1] 阻擋圖片、字型、媒體資源以加快速度
                page.route("**/*", lambda route: route.abort() 
                           if route.request.resource_type in ["image", "font", "media", "stylesheet"] 
                           else route.continue_())

                page.set_default_timeout(15000) #稍微增加超時寬容度
                
                try:
                    # [優化 2] Domcontentloaded 通常就夠了，不需要等到 networkidle (會太慢)
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    
                    # 短暫等待確保動態內容載入，但設限
                    try:
                        page.wait_for_load_state('networkidle', timeout=2000)
                    except:
                        pass
                except Exception as e:
                    print(f"頁面導航超時或錯誤: {e}")
                    return (None, None)

                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # === 提取 link_text (保留您原本的 Google News 邏輯) ===
                link_text = None
                gn_articles = soup.find_all("article", class_="MQsxIb xTewfe tXImLc R7GTQ keNKEd keNKEd VkAdve GU7x0c JMJvke q4atFc")
                if gn_articles:
                    first_article = gn_articles[0]
                    h4_element = first_article.find("h4", class_="ipQwMb ekueJc RD0gLb")
                    if h4_element:
                        link = h4_element.find("a", class_="DY5T1d RZIKme")
                        if link:
                            link_text = link.text.strip()

                # === [優化 3] DOM 清洗與去雜訊 ===
                # 移除技術性標籤
                for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'meta', 'link']):
                    tag.decompose()
                
                # 移除通常無關的版面區塊 (導航、頁尾、側邊欄)
                for tag in soup(['header', 'footer', 'nav', 'aside']):
                    tag.decompose()

                # === [優化 4] 智慧內容提取 ===
                # 如果是 Google News 頁面，我們只 Hash 那些新聞卡片的內容，忽略其他 Google 介面文字
                content_text = ""
                if gn_articles:
                    # 只將前 10 篇新聞的標題與摘要組合成 Hash 來源
                    # 這樣如果只有側邊欄廣告變了，Hash 也不會變
                    for art in gn_articles[:10]:
                        content_text += art.get_text(separator=' ', strip=True)
                else:
                    # 如果不是 Google News 結構 (可能是原始新聞頁面)，則抓取 Body
                    # 嘗試移除常見的廣告/推薦區塊
                    noise_regex = re.compile(r'ad-|advert|sidebar|menu|social|comment|footer', re.I)
                    for div in soup.find_all('div'):
                        if div.get('class') and any(noise_regex.search(str(c)) for c in div.get('class')):
                            div.decompose()
                    
                    if soup.body:
                        content_text = soup.body.get_text(separator=' ', strip=True)

                # === [優化 5] 文字正規化 (Normalization) ===
                # 1. 去除非文字字元 (只保留中英文數字)，去除標點符號造成的差異
                # 2. 轉小寫
                # 3. 去除多餘空白
                if content_text:
                    content_text = re.sub(r'[^\w\u4e00-\u9fff]+', '', content_text)
                    content_text = content_text.lower()
                
                if not content_text or len(content_text) < 50:
                    # print(f"警告: 提取內容過短，Hash 可能不準確")
                    pass

                hash_value = hashlib.md5(content_text.encode("utf-8")).hexdigest()
                return (hash_value, link_text)

        except Exception as e:
            print(f"Hash 計算過程發生錯誤: {e}")
            return (None, None)
        
        finally:
            # 確保資源釋放
            try:
                if page: page.close()
                if context: context.close()
                if browser: browser.close()
            except:
                pass

    # 在線程池中執行
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_get_hash_in_thread)
            return future.result(timeout=20) # 稍微增加總體超時時間
    except Exception as e:
        print(f"線程池執行超時或錯誤: {e}")
        return (None, None)
      
# 方案5: 檢測環境並選擇適當方法
def get_hash_smart_env(url):
    """
    智能檢測環境並選擇適當的方法
    """
    try:
        # 檢查是否在 asyncio 事件循環中
        loop = asyncio.get_running_loop()
        print("檢測到 asyncio 事件循環，使用線程池方案")
        return get_hash_sync_threaded(url)
    except RuntimeError:
        # 沒有事件循環，使用標準同步方案
        print("沒有檢測到 asyncio 事件循環，使用標準同步方案")
        return get_hash_sync(url)
    
def get_hash_sync(url):
    """
    獲取URL內容的 "特徵" hash值 - 強化版
    """
    try:
        with sync_playwright() as p:
            browser, context = create_robust_browser(p, headless=True)
            page = context.new_page()
            
            try:
                # 阻擋圖片和字型以加快速度
                page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font"] else route.continue_())
                
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                
                # 嘗試獲取 HTML
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # === 強化步驟 1: 移除網頁雜訊 (Header, Footer, Nav, Ads, Scripts) ===
                # 這些標籤通常包含變動內容，必須移除
                for tag in soup(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav', 'aside', 'form']):
                    tag.decompose()
                
                # 移除常見的干擾 Class (廣告、推薦閱讀、時間戳記)
                # 這裡使用正規表達式模糊匹配
                noise_patterns = re.compile(r'date|time|comment|share|recommend|ad-|sidebar|menu|cookie', re.I)
                for div in soup.find_all('div'):
                    if div.get('class') and any(noise_patterns.search(c) for c in div.get('class') if isinstance(c, str)):
                        div.decompose()
                
                # === 強化步驟 2: 鎖定核心內容 ===
                # 嘗試只抓取 <article> 或主要內容區塊
                content_text = ""
                
                # 優先尋找 article 標籤
                article = soup.find('article')
                if article:
                    content_text = article.get_text(separator=' ', strip=True)
                else:
                    # 如果沒有 article，嘗試找 h1 標題加上字數最多的幾個 p 標籤 (簡單的啟發式演算法)
                    h1 = soup.find('h1')
                    title_text = h1.get_text(strip=True) if h1 else ""
                    
                    # 找出所有段落，過濾掉太短的 (通常是導航或廣告文字)
                    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]
                    
                    # 組合標題和前 10 個主要段落 (這通常足夠代表文章特徵)
                    content_text = title_text + " " + " ".join(paragraphs[:10])

                # 如果真的抓不到東西，才回退到 body
                if not content_text.strip() and soup.body:
                    content_text = soup.body.get_text(separator=' ', strip=True)

                # === 強化步驟 3: 內容標準化 (Normalization) ===
                # 1. 轉小寫 (忽略大小寫差異)
                # 2. 去除所有標點符號和特殊字元 (只保留中英文數字)
                # 3. 去除多餘空白
                
                # 正規化：只保留文字與數字，去除標點符號
                content_text = re.sub(r'[^\w\u4e00-\u9fff]+', '', content_text) 
                content_text = content_text.lower()

                if len(content_text) < 50:
                    print(f"  Hash警告: 提取的內容過短 ({len(content_text)}字)，可能無法代表文章")
                    return None

                # 計算 MD5
                hash_value = hashlib.md5(content_text.encode("utf-8")).hexdigest()
                
                # 同時返回提取的文字長度供除錯
                # print(f"  [Hash Debug] 提取特徵文字: {content_text[:50]}...") 
                return hash_value

            except Exception as e:
                print(f"  Hash計算過程出錯: {e}")
                return None
            finally:
                page.close()
                context.close()
                browser.close()
                
    except Exception as e:
        print(f"獲取hash失敗: {e}")
        return None
    
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
            "crawl_date": story_data["crawl_date"],
            "country": story_data["country"]
        }
        
        # 使用 upsert 来避免重复插入
        response = supabase.table("stories").upsert(story_record, on_conflict="story_id").execute()
        print(f"   故事已保存到数据库: {story_data['story_id']}")
        return True
        
    except Exception as e:
        print(f"   保存故事到数据库失败: {e}")
        return False

def check_article_exists_in_supabase(article_url: str = "") -> bool:
    """
    檢查 cleaned_news 表中是否已存在指定的 article_url

    Args:
        article_url: 文章的最終網址

    Returns:
        True 表示已存在，False 表示不存在或查詢發生錯誤
    """
    try:
        if not article_url or not isinstance(article_url, str):
            return False

        resp = (
            supabase
            .table("cleaned_news")
            .select("article_id")
            .eq("article_url", article_url)
            .limit(1)
            .execute()
        )
        exists = bool(getattr(resp, "data", None))
        if exists:
            print(f"   cleaned_news 已存在文章: {article_url}")
        return exists
    except Exception as e:
        print(f"   檢查 cleaned_news 時發生錯誤: {e}")
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
            "story_id": story_id,
            "write_date": article_data.get("article_datetime", "")
        }
        
        # 使用 upsert 来避免重复插入
        article_url = article_data["article_url"]
        existing_article = supabase.table("cleaned_news").select("article_id").eq("article_url", article_url).execute()
        
        if existing_article.data:
            print(f"   文章已存在，跳过保存: {article_data['article_id']}")
            return True
        elif not article_data["content"] or "[清洗失敗]" in article_data["content"] or "請提供" in article_data["content"]:
            print(f"   文章内容无效，跳过保存: {article_data['article_id']}")
            return True
        elif "https://news.google.com/read" in article_data["article_url"]:
            print(f"   無法取得原始URL，跳过保存: {article_data['article_id']}")
            return True

        response = supabase.table("cleaned_news").upsert(article_record, on_conflict="article_id").execute()
        print(f"   文章已保存到数据库: {article_data['article_id']}")
        return True
        
    except Exception as e:
        print(f"   保存文章到数据库失败: {e}")
        return False

def group_articles_by_story_and_time(processed_articles, country, time_window_days=3):
    """
    根据故事分组，然后在每个故事内按时间将文章分组
    同时支持现有故事的更新功能
    
    Args:
        processed_articles: 从 get_final_content 处理后的文章列表
        time_window_days: 时间窗口天数（真正的每N天分组）
    
    Returns:
        list: 处理后的故事列表，包含 action_type 字段
    """
    taipei_tz = pytz.timezone('Asia/Taipei')

    print(f"\n=== 开始基于故事和时间分组文章 ===") 
    print(f"时间窗口: {time_window_days}天")
    
    # 按故事ID分组
    story_grouped = defaultdict(list)
    for article in processed_articles:
        story_id = article["story_id"]
        story_grouped[story_id].append(article)
    
    all_final_stories = []
    
    for story_id, articles in story_grouped.items():
        if not articles:
            continue
            
        # 获取故事基本信息（从第一篇文章）
        first_article = articles[0]
        story_title = first_article["article_title"]
        story_url = first_article["story_url"]
        story_category = first_article["story_category"]
        
        # 检查是否为现有故事更新
        existing_story_data = first_article.get("existing_story_data")
        is_existing_story = existing_story_data and first_article.get("action_type") == "add_to_existing_story"
        
        if is_existing_story:
            print(f"\n更新现有故事: {story_title}")
            print(f"   Story ID: {story_id}")
            print(f"   原有 Crawl Date: {existing_story_data.get('crawl_date', '')}")
            print(f"   原有时间范围: {existing_story_data.get('time_range', '')}")
            base_action_type = "update_existing_story"
        else:
            print(f"\n处理新故事: {story_title}")
            print(f"   Story ID: {story_id}")
            base_action_type = "create_new_story"
        
        print(f"   包含 {len(articles)} 篇文章")
        
        # 解析所有文章的时间
        articles_with_time = []
        for article in articles:
            article_datetime = article.get('article_datetime', '')
            if article_datetime and article_datetime != '':
                try:
                    parsed_dt = parser.parse(article_datetime)
                    articles_with_time.append({
                        'article': article,
                        'datetime': parsed_dt
                    })
                except (ValueError, TypeError) as e:
                    print(f"解析时间失败: {article_datetime}, 使用当前时间")
                    articles_with_time.append({
                        'article': article,
                        'datetime': datetime.now(taipei_tz)
                    })
            else:
                # 没有时间的文章使用当前时间
                articles_with_time.append({
                    'article': article,
                    'datetime': datetime.now(taipei_tz)
                })
        
        # 按时间排序
        articles_with_time.sort(key=lambda x: x['datetime'])
        
        base_start_time = None
        if is_existing_story:
            crawl_date_str = existing_story_data.get('crawl_date')
            if crawl_date_str:
                try:
                    # 1. 解析字串為 datetime
                    parsed_crawl_date = parser.parse(crawl_date_str)
                    # 2. 確保加上台北時區 (因為文章時間也都是台北時間，必須一致才能相減)
                    if parsed_crawl_date.tzinfo is None:
                        base_start_time = taipei_tz.localize(parsed_crawl_date)
                    else:
                        base_start_time = parsed_crawl_date.astimezone(taipei_tz)
                    print(f"   基準時間 (Parsed): {base_start_time}")
                except Exception as e:
                    print(f"   解析原有 crawl_date 失敗 ({crawl_date_str}): {e}，將使用新文章時間作為基準")
                    base_start_time = None

        # 执行时间窗口分组
        time_groups = _create_time_groups(articles_with_time, time_window_days, base_start_time)
        print(f"   在故事内分成 {len(time_groups)} 个时间组")

        # 为每个时间组创建最终的故事数据
        for group_idx, group in time_groups:
            # 找到组内最早和最晚的时间
            earliest_time = min(item['datetime'] for item in group)
            latest_time = max(item['datetime'] for item in group)

            # 决定使用哪个时间作为 crawl_date
            if is_existing_story:
                # 现有故事：优先使用原有的 crawl_date，如果没有则使用当前时间
                original_crawl_date = existing_story_data.get('crawl_date')
                if original_crawl_date:
                    crawl_date = original_crawl_date
                    print(f"      保持原有 Crawl Date: {crawl_date}")
                else:
                    crawl_date = earliest_time.astimezone(taipei_tz).strftime("%Y/%m/%d %H:%M")
                    print(f"      使用最早文章时间作为 Crawl Date: {crawl_date}")
            else:
                # 新故事：使用最早文章时间
                crawl_date = earliest_time.astimezone(taipei_tz).strftime("%Y/%m/%d %H:%M")
            
            # 计算实际的时间范围 - 对于现有故事，优先使用原有时间范围
            if is_existing_story and existing_story_data.get('time_range'):
                # 现有故事且有时间范围：合并新旧时间范围
                original_time_range = existing_story_data.get('time_range')
                try:
                    # 解析原有时间范围
                    if ' - ' in original_time_range:
                        orig_start_str, orig_end_str = original_time_range.split(' - ')
                        orig_start = datetime.strptime(orig_start_str, '%Y/%m/%d')
                        orig_end = datetime.strptime(orig_end_str, '%Y/%m/%d')
                    else:
                        orig_start = orig_end = datetime.strptime(original_time_range, '%Y/%m/%d')
                    
                    # 计算合并后的时间范围
                    combined_start = min(orig_start, earliest_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    combined_end = max(orig_end, latest_time.replace(hour=0, minute=0, second=0, microsecond=0))
                    
                    if combined_start.date() == combined_end.date():
                        time_range = combined_start.strftime('%Y/%m/%d')
                    else:
                        time_range = f"{combined_start.strftime('%Y/%m/%d')} - {combined_end.strftime('%Y/%m/%d')}"
                    
                    print(f"      合并时间范围: {original_time_range} + {earliest_time.strftime('%Y/%m/%d')}~{latest_time.strftime('%Y/%m/%d')} = {time_range}")
                    
                except (ValueError, TypeError) as e:
                    print(f"      解析原有时间范围失败: {original_time_range}，使用新文章时间范围")
                    # 如果解析失败，使用新文章的时间范围
                    if earliest_time.date() == latest_time.date():
                        time_range = earliest_time.strftime('%Y/%m/%d')
                    else:
                        time_range = f"{earliest_time.strftime('%Y/%m/%d')} - {latest_time.strftime('%Y/%m/%d')}"
            else:
                # 新故事或现有故事没有时间范围：使用新文章的时间范围
                if earliest_time.date() == latest_time.date():
                    time_range = earliest_time.strftime('%Y/%m/%d')
                else:
                    time_range = f"{earliest_time.strftime('%Y/%m/%d')} - {latest_time.strftime('%Y/%m/%d')}"
            
            # 生成最终的故事ID和标题
            # if len(time_groups) > 1:
            #     # 多个时间组：需要为每组生成新的ID
            #     # 新故事分组：标准的分组逻辑
            #     base_story_id = story_id[:-2] if len(story_id) >= 2 else story_id
            #     final_story_id = f"{base_story_id}{group_idx + 1:02d}"
            #     final_action_type = f"{base_action_type}_with_time_grouping"
                
            #     final_story_title = f"{story_title} (第{group_idx + 1}组)"
            # else:
            #     # 单一组：保持原有ID和标题
            #     final_story_id = story_id
            #     final_story_title = story_title
            #     final_action_type = "update_existing_story" if is_existing_story else "create_new_story"
            
            # === 5. ID 生成邏輯 (重點修改) ===
            if group_idx == 0:
                # 第 0 組 (在 crawl_date + 3天內)：保持原始 ID
                final_story_id = story_id
                final_story_title = story_title
                # 如果是現有故事，Action 是 update；如果是新故事的第0組，是 create
                final_action_type = "update_existing_story" if is_existing_story else "create_new_story"
            else:
                # 超過 3 天的組別 (index 1, 2, 3...)
                # 邏輯：生成新 ID
                final_story_id = str(uuid.uuid4())  # 使用全新 UUID 作為 ID
                final_story_title = f"{story_title} 第({group_idx + 1}組)"
                
                # 這些分出去的組別，對於資料庫來說是「新故事」
                final_action_type = "create_new_story_from_group"
                
                print(f"      [分組] 產生新 ID: {final_story_id} (原始: {story_id}, Index: {group_idx})")

            # 准备文章列表
            grouped_articles = []
            for article_idx, item in enumerate(group, 1):
                article = item['article']
                grouped_articles.append({
                    "article_id": article["id"],
                    "article_title": article["article_title"],
                    "article_index": article_idx,  # 重新编号
                    "google_news_url": article["google_news_url"],
                    "article_url": article["final_url"],
                    "media": article["media"],
                    "content": article["content"],
                    "article_datetime": article.get("article_datetime", "")
                })
            
            # 创建故事数据结构
            story_data = {
                "story_id": final_story_id,
                "story_title": final_story_title,
                "story_url": story_url,
                "crawl_date": crawl_date,
                "country": country,
                "time_range": time_range,
                "category": story_category,
                "articles": grouped_articles,
                "action_type": final_action_type,
                "is_time_grouped": len(time_groups) > 1,
                "group_index": group_idx + 1 if len(time_groups) > 1 else None,
                "total_groups": len(time_groups) if len(time_groups) > 1 else None
            }
            
            # 如果是现有故事，保留更多原有数据的参考
            if group_idx == 0 and is_existing_story:
                story_data["original_story_data"] = existing_story_data
                story_data["time_range_updated"] = existing_story_data.get('time_range') != time_range
                story_data["crawl_date_preserved"] = existing_story_data.get('crawl_date') == crawl_date
            
            all_final_stories.append(story_data)
            
            # 计算实际天数跨度
            actual_days = (latest_time.date() - earliest_time.date()).days + 1
            
            if len(time_groups) > 1:
                print(f"   时间组 {group_idx + 1}: {time_range} (实际跨度: {actual_days}天)")
            else:
                print(f"   完整故事: {time_range} (实际跨度: {actual_days}天)")
            
            print(f"      最终 Story ID: {final_story_id}")
            print(f"      Crawl Date: {crawl_date}")
            print(f"      文章数: {len(grouped_articles)} 篇")
            print(f"      处理类型: {final_action_type}")
    
    print(f"\n总共处理完成 {len(all_final_stories)} 个最终故事")
    return all_final_stories

# def _create_time_groups(articles_with_time, time_window_days):
#     """
#     根据时间窗口将文章分组的内部函数
#     """
#     time_groups = []
#     current_group = []
#     current_group_start_time = None
#     current_group_end_time = None
    
#     for item in articles_with_time:
#         article_time = item['datetime']
        
#         if current_group_start_time is None:
#             # 第一篇文章，开始第一组
#             current_group_start_time = article_time
#             current_group_end_time = article_time + timedelta(days=time_window_days)
#             current_group.append(item)
#             print(f"      开始新组: {current_group_start_time.strftime('%Y/%m/%d %H:%M')} - {current_group_end_time.strftime('%Y/%m/%d %H:%M')}")
#         else:
#             # 检查是否在当前组的时间窗口内
#             if article_time < current_group_end_time:
#                 # 在同一组内
#                 current_group.append(item)
#                 print(f"         加入当前组: {article_time.strftime('%Y/%m/%d %H:%M')}")
#             else:
#                 # 超出时间窗口，开始新的一组
#                 if current_group:
#                     time_groups.append(current_group)
#                     print(f"      完成组别，包含 {len(current_group)} 篇文章")
                
#                 # 开始新组
#                 current_group = [item]
#                 current_group_start_time = article_time
#                 current_group_end_time = article_time + timedelta(days=time_window_days)
#                 print(f"      开始新组: {current_group_start_time.strftime('%Y/%m/%d %H:%M')} - {current_group_end_time.strftime('%Y/%m/%d %H:%M')}")
    
#     # 添加最后一组
#     if current_group:
#         time_groups.append(current_group)
#         print(f"      完成最后组别，包含 {len(current_group)} 篇文章")
    
#     return time_groups

def _create_time_groups(articles_with_time, time_window_days, base_start_time=None):
    """
    根據基準時間將文章分組。
    如果提供了 base_start_time (現有故事)，則以該時間為錨點，每3天切一組。
    如果沒有 (新故事)，則以第一篇文章為錨點。
    
    Returns:
        dict: { group_index: [articles] } 
        group_index 0 = 原始故事 (0~3天)
        group_index 1 = 第2組 (3~6天)
        ...
    """
    groups = defaultdict(list)
    
    # 定義時區 (雖然我們主要靠 astimezone 自動轉換，但定義一下以防萬一)
    taipei_tz = pytz.timezone('Asia/Taipei')

    # 如果沒有提供基準時間，就用第一篇文章的時間 (針對新故事)
    if base_start_time is None and articles_with_time:
        base_start_time = articles_with_time[0]['datetime']
        print(f"      使用新故事的基準時間 (crawl_date): {base_start_time.strftime('%Y/%m/%d %H:%M')}")
    else:
        print(f"      使用提供的基準時間 (crawl_date): {base_start_time.strftime('%Y/%m/%d %H:%M')}")

    if not articles_with_time:
        return []

    # === 防呆 1: 確保 base_start_time 是有時區的 (Aware) ===
    if base_start_time.tzinfo is None:
        # 如果它是 Naive，假設它是台北時間
        base_start_time = taipei_tz.localize(base_start_time)
    print(f"      基準時間 (crawl_date): {base_start_time.strftime('%Y/%m/%d %H:%M')}")

    for item in articles_with_time:
        article_time = item['datetime']
        
        if article_time.tzinfo is None:
            article_time = taipei_tz.localize(article_time)
        else:
            # 如果原本就有時區，轉成跟 base 一樣的時區以確保可以相減
            article_time = article_time.astimezone(base_start_time.tzinfo)

        # 計算這篇文章距離基準時間幾天
        try:
            time_diff = article_time - base_start_time
            days_diff = time_diff.total_seconds() / (24 * 3600)
            
            if days_diff < 0:
                group_index = 0
            else:
                group_index = int(days_diff // time_window_days)
                
            groups[group_index].append(item)
            # Log 方便除錯
            print(f"      文章時間: {article_time}, 距離基準: {days_diff:.1f}天 -> 分入第 {group_index + 1} 組")
        except Exception as e:
            print(f"      [錯誤] 時間計算失敗: {e}")
            # 發生錯誤時，默認歸到第0組，避免程式崩潰
            groups[0].append(item)

    # 將字典轉換回列表，並按 index 排序，確保回傳順序正確
    # 這裡回傳格式改為 list of tuples: [(index, articles), (index, articles)...]
    # 這樣我們在外面才能知道他是第幾組
    sorted_groups = sorted(groups.items())
    
    return sorted_groups

def save_stories_to_supabase(stories):
    """
    批量保存故事和文章到Supabase数据库
    """
    try:
        saved_stories = 0
        updated_stories = 0
        saved_articles = 0
        
        for story in stories:
            story_id = story["story_id"]
            action_type = story.get("action_type", "create_new_story")
            
            # 根据 action_type 决定如何处理故事
            if action_type.startswith("create_new_story"):
                # 保存新故事
                if save_story_to_supabase(story):
                    saved_stories += 1
            elif action_type.startswith("update_existing_story"):
                # 更新现有故事的 crawl_date
                try:
                    update_data = {
                        "crawl_date": story["crawl_date"]
                    }
                    # response = supabase.table("stories").update(update_data).eq("story_id", story_id).execute()
                    print(f"   故事 crawl_date 已更新: {story_id}")
                    updated_stories += 1
                except Exception as e:
                    print(f"   更新故事 crawl_date 失败: {e}")
            
            # 保存文章（无论是新故事还是现有故事）
            for article in story["articles"]:
                if save_article_to_supabase(article, story_id):
                    saved_articles += 1
        
        print(f"批量保存完成: {saved_stories} 个新故事, {updated_stories} 个更新故事, {saved_articles} 篇文章")
        return True
        
    except Exception as e:
        print(f"批量保存到Supabase时出错: {e}")
        return False

def save_stories_to_json(stories, filename):
    """
    将故事数据保存到JSON文件
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stories, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False
    
def process_news_pipeline(main_url, country, category):
    """
    完整的新聞處理管道 - 修正版本
    主要修正：確保 Playwright 資源在整個處理過程中正確管理
    """
    print(f"开始处理 {category} 分类的新闻...")
    
    # 步驟1: 獲取所有故事連結
    story_links = get_main_story_links(main_url, country, category)
    if not story_links:
        print("没有找到任何故事连结")
        return []
    
    # 步驟2: 處理每個故事，獲取所有文章連結
    all_article_links = []
    if(category=="Politics" or category=="International News" or category=="Science & Technology" or category=="Business & Finance"):
        for story_info in story_links[:4]:
            article_links = get_article_links_from_story(story_info)
            all_article_links.extend(article_links)
    else:
        for story_info in story_links[:3]:
            article_links = get_article_links_from_story(story_info)
            all_article_links.extend(article_links)
    
    if not all_article_links:
        print("没有找到任何文章连结")
        return []
    
    print(f"\n总共收集到 {len(all_article_links)} 篇文章待处理")
    
    # 步驟3: 獲取每篇文章的完整內容 - 重要修正
    final_articles = []
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    # 使用單一的 Playwright 實例來處理所有文章
    with sync_playwright() as p:
        browser = None
        context = None
        page = None
        
        try:
            # 創建初始的 browser, context, page
            browser, context = create_robust_browser(p, headless=True)
            page = context.new_page()
            initialize_page_with_cookies(page)
            
            for i, article_info in enumerate(all_article_links, 1):
                print(f"\n处理文章 {i}/{len(all_article_links)}: {article_info['article_title']}")
                print(f"story_id: {article_info.get('story_id', 'N/A')}")
                
                # 檢查 page 是否仍然有效
                try:
                    current_title = page.title()
                except Exception as e:
                    print(f"   Page 异常，重新创建: {e}")
                    try:
                        if page:
                            page.close()
                        if context:
                            context.close()
                        if browser:
                            browser.close()
                    except:
                        pass
                    
                    # 重新創建
                    browser, context = create_robust_browser(p, headless=True)
                    page = context.new_page()
                    initialize_page_with_cookies(page)
                
                # 處理文章
                article_content = get_final_content(article_info, page)
                
                if article_content:
                    final_articles.append(article_content)
                    print(f"   成功获取内容")
                    consecutive_failures = 0
                else:
                    print(f"   无法获取内容")
                    consecutive_failures += 1
                    
                    # 連續失敗處理
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"   连续 {consecutive_failures} 次失败，重新创建 Browser/Page...")
                        
                        try:
                            if page:
                                page.close()
                            if context:
                                context.close()
                            if browser:
                                browser.close()
                        except:
                            pass
                        
                        browser, context = create_robust_browser(p, headless=True)
                        page = context.new_page()
                        initialize_page_with_cookies(page)
                        consecutive_failures = 0
                
                time.sleep(random.randint(2, 4))
                
        except KeyboardInterrupt:
            print(f"\n用户中断处理")
        except Exception as e:
            print(f"\n处理过程中发生严重错误: {e}")
        finally:
            # 確保清理所有資源
            try:
                if page:
                    page.close()
                if context:
                    context.close()
                if browser:
                    browser.close()
                print("Playwright 資源清理完成")
            except Exception as e:
                print(f"Playwright 清理时出现问题: {e}")
    
    print(f"\n文章内容获取完成: 成功 {len(final_articles)}/{len(all_article_links)} 篇")
    
    # 步驟4: 按故事和時間分組
    final_stories = group_articles_by_story_and_time(final_articles, country, time_window_days=3)
    
    return final_stories

def initialize_page_with_cookies(page):
    """初始化 Playwright Page 并加载 cookies"""
    try:
        # 先访问 Google News 主页
        page.goto("https://news.google.com/")
        time.sleep(2)
        
        # 尝试加载 cookies
        try:
            with open("cookies2.json", "r", encoding="utf-8") as f:
                cookies = json.load(f)
            
            # 转换 cookies 格式为 Playwright 格式
            playwright_cookies = []
            for cookie in cookies:
                playwright_cookie = {
                    "name": cookie.get("name"),
                    "value": cookie.get("value"),
                    "domain": cookie.get("domain", ".google.com"),
                    "path": cookie.get("path", "/"),
                }
                
                # 添加可选字段
                if "expires" in cookie:
                    playwright_cookie["expires"] = cookie["expires"]
                if "httpOnly" in cookie:
                    playwright_cookie["httpOnly"] = cookie["httpOnly"]
                if "secure" in cookie:
                    playwright_cookie["secure"] = cookie["secure"]
                    
                playwright_cookies.append(playwright_cookie)
            
            # 添加 cookies 到页面上下文
            page.context.add_cookies(playwright_cookies)
            print("Cookies 加载完成")
            
        except FileNotFoundError:
            print("cookies.json 文件不存在，使用默认设置")
        except Exception as e:
            print(f"加载 cookies 时出错: {e}")
    
    except Exception as e:
        print(f"初始化 Page cookies 时出错: {e}")

def main():
    """
    主函數 - 新聞爬蟲的入口點
    """
    print("="*80)
    print(" Google News 爬蟲程序啟動")
    print("="*80)

    # 配置需要處理的新聞分類
    news_sources = {
        # 新增日本分類
        "Japan": {
            # "Politics": {
            #     "url": "https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRFZ4ZERBU0FtcGhLQUFQAQ?hl=ja&gl=JP&ceid=JP%3Aja",
            # },
            # "International News": {
            #     "url": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtcGhHZ0pLVUNnQVAB?hl=ja&gl=JP&ceid=JP%3Aja",
            # },
            "Science & Technology": {
                "url": "https://news.google.com/topics/CAAqKAgKIiJDQkFTRXdvSkwyMHZNR1ptZHpWbUVnSnFZUm9DU2xBb0FBUAE?hl=ja&gl=JP&ceid=JP%3Aja",
            },
            "Entertainment": {
                "url": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtcGhHZ0pLVUNnQVAB?hl=ja&gl=JP&ceid=JP%3Aja"
            },
            # "Lifestyle & Consumer": {
            #     "url": "https://news.google.com/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR2hvWkdJU0FtcGhLQUFQAQ?hl=ja&gl=JP&ceid=JP%3Aja"
            # },
            # "Sports": {
            #     "url": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtcGhHZ0pLVUNnQVAB?hl=ja&gl=JP&ceid=JP%3Aja"
            # },
            "Business & Finance": {
                "url": "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtcGhHZ0pLVUNnQVAB?hl=ja&gl=JP&ceid=JP%3Aja"
            },
            "Health & Wellness": {
                "url": "https://news.google.com/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNREpqYlRZeEVnSnFZU2dBUAE?hl=ja&gl=JP&ceid=JP%3Aja"
            },
        }
    }


    
    # 可以選擇處理特定分類或全部分類
    selected_countries = list(news_sources.keys())   # 預設處理全部 country
    selected_categories = None  # None = 處理各 country 的全部分類

    try:
        for country in selected_countries:
            print(f"\n{'#' * 40}\n開始處理國家：{country}\n{'#' * 40}")
            categories = news_sources[country]
                
            for category, info in categories.items():
                all_final_stories = []
                start_time = time.time()
                if selected_categories and category not in selected_categories:
                    continue

                category_start = time.time()
                print(f"\n{'='*60}\n開始處理分類: {category}\n{'='*60}")

                try:
                    url = info["url"]
                    category_stories = process_news_pipeline(url, country, category)
                    if category_stories:
                        all_final_stories.extend(category_stories)
                        print(f"✅ {category} 處理完成，共獲得 {len(category_stories)} 則故事")
                    else:
                        print(f"⚠️ {category} 無結果")
                except Exception as e:
                    print(f"❌ {category} 處理錯誤: {e}")

                time.sleep(5)  # 小延遲防止過快請求
                print(f"耗時: {time.time() - category_start:.2f} 秒")

                print(f"\n{country} 處理完成，總故事數：{len(all_final_stories)}")
                print("-" * 60)

                # 🧹 清理與保存
                if all_final_stories:
                    try:
                        cleaned = clean_data(all_final_stories)
                        save_stories_to_supabase(cleaned)
                        print(f"✅ {country} 數據已保存至 Supabase")
                    except Exception as e:
                        print(f"⚠️ 保存失敗: {e}")

                print(f"{country} 總耗時: {(time.time()-start_time):.2f} 秒")

    except KeyboardInterrupt:
        print("\n 使用者中斷程序，正在安全退出...")
    except Exception as e:
        import traceback
        print(f"⚠️ 執行錯誤: {e}\n{traceback.format_exc()}")
    finally:
        print("\n" + "="*80)
        print("Google News 爬蟲程序結束")
        print("="*80)


if __name__ == "__main__":
    main() 