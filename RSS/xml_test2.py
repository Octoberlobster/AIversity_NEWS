# 整合五份程式碼
# 只保留一小時內的新聞
import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs

# 設定 RSS 來源
sources = {
    "UDN": "https://udn.com/news/rssfeed/",
    "NewTalk": "https://newtalk.tw/rss/all/",
    "LTN": "https://news.ltn.com.tw/rss/all.xml",
    "CNA": "https://feeds.feedburner.com/rsscna/politics",
    "CNA": "https://feeds.feedburner.com/rsscna/intworld",
    "CNA": "https://feeds.feedburner.com/rsscna/mainland",
    "CNA": "https://feeds.feedburner.com/rsscna/finance",
    "CNA": "https://feeds.feedburner.com/rsscna/technology",
    "CNA": "https://feeds.feedburner.com/rsscna/lifehealth",
    "CNA": "https://feeds.feedburner.com/rsscna/social",
    "CNA": "https://feeds.feedburner.com/rsscna/local",
    "CNA": "https://feeds.feedburner.com/rsscna/culture",
    "CNA": "https://feeds.feedburner.com/rsscna/sport",
    "CNA": "https://feeds.feedburner.com/rsscna/stars",
    "TTV": "https://www.ttv.com.tw/rss/RSSHandler.ashx?d=news",
}

news_data = []
current_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # 轉換為台灣時間
one_hour_ago = current_time - datetime.timedelta(hours=1)

for source, url in sources.items():
    feed = feedparser.parse(url)
    
    for entry in feed.entries:  
        # 解析時間
        t = entry.published_parsed
        dt = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        dt += datetime.timedelta(hours=8)  # 調整時區
        
        if dt < one_hour_ago:  # 只保留一小時內的新聞
            continue
        
        news = {
            "Source": source,
            "Title": entry.title,
            "URL": entry.link,
            "Date": dt.strftime("%Y/%m/%d %H:%M"),
        }
        
        # 嘗試抓取圖片
        image_url = None
        if "enclosures" in entry and entry.enclosures:
            image_url = entry.enclosures[0].href
        elif "media_content" in entry:
            image_url = entry.media_content[0]["url"][5:]
        elif "description" in entry:
            soup = BeautifulSoup(entry.description, "html.parser")
            img_tag = soup.find("img")
            if img_tag:
                parsed_url = urlparse(img_tag["src"])
                query_params = parse_qs(parsed_url.query)
                image_url = query_params.get("u", [""])[0]
        news["Image"] = image_url or ""
        
        # 取得新聞內文
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
        }
        content = requests.get(entry.link, headers=headers)
        content.encoding = "utf-8"
        if content.status_code == 200:
            soup = BeautifulSoup(content.text, "html.parser")
            body_content = str(soup.body)
            news["Content"] = body_content

            if not image_url:
                img_url = None
                try:
                    if source == "CNA":
                        img_tag = soup.find_all("div", class_="fullPic")
                    elif source == "TTV":
                        img_tag = soup.find_all("div", class_="article-body")
                    elif source == "LTN":
                        img_tag = soup.find_all("div", class_="photo boxTitle")
                    else:
                        img_tag = []

                    for img in img_tag:
                        img_url = img.find("img")["src"]
                        break
                except:
                    img_url = ""

                news["Image"] = img_url
        print(news)
        news_data.append(news)

# 儲存數據
timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
json_path = f"json/{timestamp}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=4)

print(f"新聞資料已儲存至 {json_path}，共 {len(news_data)} 則新聞")
