# 台視ttv rss feed 半小時內新聞
import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs

# 取得 RSS Feed
url = "https://udn.com/news/rssfeed/"
feed = feedparser.parse(url)
news_data = []

# 遍歷新聞項目
for entry in feed.entries:  
    news = {}
    print(f"標題: {entry.title}")
    news["title"] = entry.title
    print(f"連結: {entry.link}")
    news["url"] = entry.link

    image_url = None
    # # 嘗試從 enclosure 中取得圖片
    if "enclosures" in entry and entry.enclosures:
        image_url = entry.enclosures[0].href  # enclosure 的 href 屬性通常是圖片連結

    # 嘗試從 media:content 中取得圖片
    elif not image_url and "media_content" in entry:
        image_url = entry.media_content[0]["url"]  # media:content 的 url 屬性
    
    # 嘗試解析 description 內的圖片
    elif "description" in entry:
        soup = BeautifulSoup(entry.description, "html.parser")
        img_tag = soup.find("img")
        if img_tag:
            # 解析 URL 參數
            parsed_url = urlparse(img_tag["src"])
            query_params = parse_qs(parsed_url.query)

            # 取得真正的圖片連結
            jpg_url = query_params.get("u", [""])[0]
            image_url = jpg_url
    else:
        image_url = ""
    news["image"] = image_url
    print(f"圖片: {image_url}\n")

    t = entry.published_parsed
    # 轉換為 datetime 物件
    dt = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
    # 增加 8 小時
    dt += datetime.timedelta(hours=8)
    # 轉換成指定格式
    formatted_time = dt.strftime("%Y/%m/%d %H:%M")
    print(f"時間: {formatted_time}")
    news["date"] = formatted_time

    content = requests.get(entry.link)
    content.encoding = "utf-8"
    if content.status_code == 200:
        soup = BeautifulSoup(content.text, "html.parser")
        body_content = str(soup.body)  # 提取 <body> 內的所有 HTML 內容
        news["content"] = body_content  # 儲存原始 HTML 內容
    print()
    news_data.append(news)

# 儲存數據
timestamp = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
json_path = f"json/{timestamp}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=4)

print(f"新聞資料已儲存至 {json_path}")

