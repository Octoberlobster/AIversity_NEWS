# 有排程
import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs
# import schedule
import json
import schedule
from supabase import create_client, Client
import uuid
import os
import certifi
import urllib3

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings()

# === Supabase 設定 ===
# 初始化 Supabase 連線
SUPABASE_URL         = os.getenv("API_KEY_URL")
SUPABASE_SERVICE_KEY = os.getenv("API_KEY_supa")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
# === 欄位對應 ===
key_map = {
    "title": "title",
    "Title": "title",
    "url": "url",
    "URL": "url",
    "Date": "date",
    "date": "date",
    "content": "content",
    "translatedcontent": "content",
    "Content": "content",
    "Source": "sourcecle_media",
    "source": "sourcecle_media",
    "Image": "image",
}

# 設定 RSS 來源
sources = {
    "UDN": "https://udn.com/news/rssfeed/",
    "ETtoday": "https://feeds.feedburner.com/ettoday/realtime",
    "NewTalk": "https://newtalk.tw/rss/all/",
    # "LTN": "https://news.ltn.com.tw/rss/all.xml",
    "CNA": [
        "https://feeds.feedburner.com/rsscna/politics",
        "https://feeds.feedburner.com/rsscna/intworld",
        "https://feeds.feedburner.com/rsscna/mainland",
        "https://feeds.feedburner.com/rsscna/finance",
        "https://feeds.feedburner.com/rsscna/technology",
        "https://feeds.feedburner.com/rsscna/lifehealth",
        "https://feeds.feedburner.com/rsscna/social",
        "https://feeds.feedburner.com/rsscna/local",
        "https://feeds.feedburner.com/rsscna/culture",
        "https://feeds.feedburner.com/rsscna/sport",
        "https://feeds.feedburner.com/rsscna/stars",
    ],
    # "TTV": "https://www.ttv.com.tw/rss/RSSHandler.ashx?d=news",
}

def normalize_key(key):
    lower_key = key.lower()
    return key_map.get(lower_key, lower_key)

def transform_single(obj):
    if isinstance(obj, dict):
        new_obj = {normalize_key(k): transform_single(v) for k, v in obj.items()}
        new_obj["sourcecle_id"] = generate_uuid(obj.get("sourcecle_id", ""))
        return new_obj
    elif isinstance(obj, list):
        return [transform_single(item) for item in obj]
    else:
        return obj

def transform_all(data):
    return [transform_single(item) for item in data[:400]]

def generate_uuid(val):
    try:
        # 若是合法 UUID 字串，轉成 UUID 沒問題
        return str(uuid.UUID(val))
    except:
        # 若不是，就新產一個 UUID
        return str(uuid.uuid4())

def fetch_UDN_news_content_and_images(news_url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        'Cookie': 'et_token=d6a74655ea77caa8825e10b8d25a397c; _gid=GA1.2.2091710780.1750162757; dable_uid=22808593.1746544424455; _ss_pp_id=cea52eba14de7e10a221746503053891; _cc_id=4e771a1433eefa6a246c28513242588e; panoramaId_expiry=1750767573487; panoramaId=1e4bc676978f8f93a197d9f0634116d539385dd3e9f4327377fd04143d7cc427; panoramaIdType=panoIndiv; _id5_uid=ID5-2077EMsl3hZ2tyBrocTT2gxHJUrBr1WooHMM-hRN1g; check_pc_mobile=pc; et_client_country=TW; et_client_country_set=Y; et_track=MTExLjE4NC4xMDkuMTZ8fEhvbWVwbHVzfHxUV3x8; et_tag=OHxH; pbjs-unifiedid=%7B%22TDID%22%3A%22a4861716-78e0-44ad-b679-01940d2306d5%22%2C%22TDID_LOOKUP%22%3A%22TRUE%22%2C%22TDID_CREATED_AT%22%3A%222025-05-17T12%3A24%3A03%22%7D; pbjs-unifiedid_cst=zix7LPQsHA%3D%3D; oid=%257B%2522oid%2522%253A%2522255ffa09-2a6d-11f0-a6d2-0242ac120002%2522%252C%2522ts%2522%253A-62135596800%252C%2522v%2522%253A%252220201117%2522%257D; dcs_local_cid=a2sf0ypryl; _scor_uid=32319d529c944bdb8c3ed78bb09905ca; dcs_cookie_id=o31ez71rs6; __htid=d5f65056-9d8f-4ff2-882e-eb483868486d; _fbp=fb.2.1750163055096.886552306; liveShowClose=0; PHPSESSID=6ia42odk2if328needjvc8akpc; adE04-114680=1; PCInread_Ad_finance=1; PCInread_Ad_finance-expire=Wed%20Jun%2018%202025%2013%3A34%3A26%20GMT%2B0800%20(%E5%8F%B0%E5%8C%97%E6%A8%99%E6%BA%96%E6%99%82%E9%96%93); trc_cookie_storage=taboola%2520global%253Auser-id%3Dcb3f91f6-d376-4188-ba71-69f37982dfea-tuctf130bf3; __gads=ID=64a6ba4e107dd2f5:T=1750162788:RT=1750221284:S=ALNI_MZ-HNSfG0770r0OO6raaTupFw9MRw; __gpi=UID=00001131199a9e91:T=1750162788:RT=1750221284:S=ALNI_MY59nMv6NO6kViTp3TWatuURfyLYw; _ht_hi=1; _ht_em=1; __eoi=ID=827b2f3714aa4c5f:T=1750162759:RT=1750221272:S=AA-Afjadd5RwQyP0hFMSobccWH50; _ga=GA1.1.428563548.1750162757; cto_bundle=UI3Cg183MjJrMW5jbW1Yb1h0aFBzNzdZWEFjSWd6VWpWJTJCeFRWalVtVHBFQldPb29sJTJCJTJCJTJCUkFpWnU1WjZOcGVLQjIlMkZGTVZiTzgyMlVPTmpPaHIzVlBMazYxUmVpWmZxRDNNVndrU2dleEQlMkJ3MkVFVXpWOUJIbnlDVXE5MHEzNSUyQm5ZRnJNajZqTTFQNWs5WmJOSSUyRk5haFlhcVAyaWgxeU9JTkxXbE9aSnJ1TjlDekFFZ0lkVjdycmZCcSUyQkdaVkFkOXJGJTJGRjY2QkRCYWs4ZkhFdUlSMEJtZ2huM1ElM0QlM0Q; FCNEC=%5B%5B%22AKsRol_LdUAPCRghnWxuivUhUsjp4sxvAVM9fy3S1B1RImGKyEWJmkTY8FEsw5SdBVjzofOaVNcRhR-7ei2zEfgh9n6l7Aik2GKXo2IDYqpZTcjweuu0hNR4BgCuMdghtbO0jFLMLi-YElce5kIwR9xzQbu7asv5gg%3D%3D%22%5D%5D; _ga_KD7QNC2PBP=GS2.1.s1750221456$o1$g1$t1750221512$j4$l0$h0; _ga_EK0KZ2R7Q6=GS2.1.s1750221267$o3$g1$t1750221512$j36$l0$h0; _ga_GVJ4QQ3W90=GS2.1.s1750221284$o1$g0$t1750221533$j60$l0$h0; _td=010155a2-cf12-4e33-83ac-bc5259b0aba3; _ga_884QZTRRNY=GS2.1.s1750221893$o1$g0$t1750221893$j60$l0$h0; _ga_DJCCTPSJDT=GS2.1.s1750221928$o1$g0$t1750221928$j60$l0$h0; _ga_RWKNJXB8LF=GS2.1.s1750221944$o1$g1$t1750222196$j60$l0$h0',
        'Connection': 'close',  # 關閉連線以避免 Keep-Alive
    }
    # 禁用 SSL 警告
    # urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        response = requests.get(news_url, headers=headers, timeout=10)#, verify=False)
        response.encoding = "utf-8"
        print(f"訪問新聞: {news_url}，狀態碼: {response.status_code}")
        # print(f"訪問新聞內文: {response.text}")

        if response.status_code != 200:
            print("❌ 無法訪問新聞內文")
            return ""
        
        try:
            # 先嘗試完整解析
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 統一使用 find_all() 返回列表
            content_section = (
                soup.find_all('div', attrs={'data-desc': '內文'}) or 
                soup.find_all('div', attrs={'data-desc': '內容頁'}) or
                soup.find_all('div', class_='text boxTitle boxText') or
                soup.find_all('div', class_='paragraph') or
                soup.find_all('section', class_='article-content__editor') or
                soup.find_all('div', class_='story')
            )
            
            # 如果沒有找到內容，嘗試從特定位置開始解析
            if not content_section:
                soup = BeautifulSoup(response.text[50000:], 'html.parser')
                content_section = (
                    soup.find_all('div', attrs={'data-desc': '內文'}) or 
                    soup.find_all('div', attrs={'data-desc': '內容頁'}) or
                    soup.find_all('div', class_='text boxTitle boxText') or
                    soup.find_all('section', class_='article-content__editor') or
                    soup.find_all('div', class_='story')
                )
        except Exception as e:
            print(f"❌ 解析 HTML 時發生錯誤: {e}")
            return "", []

        content = []
        if content_section:
            for section in content_section:
                paragraphs = section.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if any(kw in text for kw in ["延伸閱讀", "責任編輯", "核稿編輯", "▪", "不用抽", "【", "一手掌握經濟脈動", "本網站之文字"]):
                        break
                    elif (p.find('iframe') or 
                        'APP' in p.text or 
                        '點我下載APP' in p.text or 
                        '活動辦法' in p.text or
                        '請繼續往下閱讀' in p.text or
                        '圖／' in p.text or
                        '／桃園報導' in p.text or
                        '／台東報導' in p.text or
                        '／台北報導' in p.text or
                        '資料照／' in p.text or
                        '中央社記者' in p.text or
                        '記者宋健生/攝影' in p.text or
                        '／攝影' in p.text or
                        '／翻攝' in p.text or
                        '／台南報導' in p.text or
                        '／台中報導' in p.text or
                        '／綜合報導' in p.text or
                        '／新北報導' in p.text or
                        '／高雄報導' in p.text or
                        '／彰化報導' in p.text or
                        '▲' in p.text or
                        '圖文／CTWANT' in p.text or
                        '／編譯' in p.text):
                        continue
                    else:
                        content.append(text)
        else:
            print("找不到指定的內容區域")

        content_str = " ".join(content)
        return content_str

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return "", []

def fetch_NewTalk_news_content_and_images(content_str: str):
    content = []
    soup = BeautifulSoup(content_str, 'html.parser') 
    if soup:
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if any(kw in text for kw in ["延伸閱讀", "責任編輯", "核稿編輯", "▪", "本網站之文字"]):
                break
            elif '中央社記者' in p.text or '圖為' in p.text :
                continue
            content.append(text)
    else:
        print("找不到指定的內容區域")

    content_str = " ".join(content)
    return content_str

def fetch_LTN_CNA_image(news_url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(news_url, headers=headers, timeout=10, verify=False)
        response.encoding = "utf-8"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text[30000:], 'html.parser')
            img_tag = soup.find("div", class_="image-popup-vertical-fit") or soup.find("div", class_="fullPic")
            if img_tag:
                # 先檢查是否有 href 屬性
                if img_tag.has_attr('href'):
                    return img_tag["href"]
                
                # 如果沒有 href，則尋找內部的 img 標籤
                img_element = img_tag.find('img')
                if img_element and img_element.has_attr('src'):
                    print(img_element['src'])
                    return img_element['src']
                
                # 如果沒有 src，檢查 data-src
                if img_element and img_element.has_attr('data-src'):
                    return img_element['data-src']
            
            # 如果上述都找不到，搜尋文章內容中的圖片
            for p in soup.select('div.text.boxTitle.boxText p'):
                img = p.find('img')
                if img and img.has_attr('data-src'):
                    main_img = img['data-src']
                    return main_img
                elif img and img.has_attr('src'):
                    return img['src']
                
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    return ""

def crawl_news():
    news_data = []
    current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # 轉換為台灣時間
    one_hour_ago = current_time - datetime.timedelta(hours=1)

    for source, url in sources.items():
        if isinstance(url, list):
            urls = url
        else:
            urls = [url]

        for url in urls:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                if "現場直播中" in entry.get("title"):
                    print(f"跳過現場直播新聞: {entry.title}")
                    continue
                # 優先使用 published_parsed
                if entry.get("published_parsed"):
                    t = entry.published_parsed
                    dt = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                elif entry.get("published"):  # 嘗試用 published 字串補救
                    try:
                        date_str = entry.published.replace(',', ', ')  # 修復缺空格問題
                        t_struct = time.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                        dt = datetime.datetime.fromtimestamp(time.mktime(t_struct))
                    except Exception as e:
                        print(f"⚠️ 無法解析 published 字串: {entry.published}，錯誤: {e}")
                        dt = None
                else:
                    print("⚠️ 沒有 published 或 published_parsed")
                    dt = None

                # 加時區補正
                if dt and source in ["CNA", "UDN", "NewTalk"]:
                    dt = dt + datetime.timedelta(hours=8) 
                    print("發布時間：", dt.strftime("%Y/%m/%d %H:%M"))
                
                if dt < one_hour_ago:  # 只保留一小時內的新聞
                    continue
                
                # 從 RSS 爬取 標題/連結/日期
                news = {
                    "source": source,
                    "title": entry.title,
                    "url": entry.link,
                    # "date": dt.strftime("%Y/%m/%d %H:%M"),
                    "date": entry.pubDate if "pubDate" in entry else dt.strftime("%Y/%m/%d %H:%M"),
                    "content": ''
                }
                
                # 嘗試抓取圖片
                image_url = None
                if "enclosures" in entry and entry.enclosures:
                    image_url = entry.enclosures[0].href
                elif "media_content" in entry:
                    image_url = entry.media_content[0]["url"][5:]
                elif "description" in entry:  # UDN 的新聞有圖片在 description 中
                    soup = BeautifulSoup(entry.description, "html.parser")
                    img_tag = soup.find("img")
                    if img_tag:
                        parsed_url = urlparse(img_tag["src"])
                        query_params = parse_qs(parsed_url.query)
                        image_url = query_params.get("u", [""])[0]
                if( not image_url):
                    image_url = fetch_LTN_CNA_image(entry.link)
                news["image"] = image_url or ""
                
                # 嘗試抓取新聞內文
                if source == "UDN" or source == "ETtoday" or source == "LTN" or source == "CNA":
                    content_str = fetch_UDN_news_content_and_images(entry.link)
                elif source == "NewTalk":
                    content_str = fetch_NewTalk_news_content_and_images(entry.description)
                else:
                    content_str = ""
                news["content"] = content_str
                print(news, "\n")
                news_data.append(news)

        # # 儲存數據
        timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
        json_path = f"json/{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(news_data, f, ensure_ascii=False, indent=4)

        print(f"新聞資料已儲存至 {json_path}，共 {len(news_data)} 則新聞")

        # # === 載入 JSON ===
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # # === 處理轉換 ===
        converted_data = transform_all(raw_data)

        # # === 匯入 Supabase ===
        try:
            # 使用 upsert，on_conflict 指定衝突時的處理方式
            for item in converted_data:
                res = supabase.table("cleaned_news").upsert(
                    item,
                    on_conflict="title"  # 以 title 為衝突檢查欄位
                ).execute()
            print(f"✅ 資料處理完成，共處理 {len(converted_data)} 筆")
        except Exception as e:
            print("❌ 匯入失敗：", e)


crawl_news()
# 設定排程
# schedule.every(59).minutes.do(crawl_news)  # 每 59 分鐘執行一次

# while True:
#     schedule.run_pending()  # 執行排程內的任務
#     time.sleep(5)  # 避免 CPU 高負載