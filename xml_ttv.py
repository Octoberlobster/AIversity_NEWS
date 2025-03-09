# 台視ttv rss feed 半小時內新聞
import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json

# 取得 RSS Feed
url = "https://www.ttv.com.tw/rss/RSSHandler.ashx?d=news"
feed = feedparser.parse(url)
news_data = []

# 遍歷新聞項目
for entry in feed.entries:  
    news = {}
    print(f"標題: {entry.title}")
    news["title"] = entry.title
    print(f"連結: {entry.link}")
    news["url"] = entry.link

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

        img_url = None
        try:
            img_tag = soup.find_all("div", class_="article-body")
            for img in img_tag:
                img_url = img.find("img")["src"]
                break
        except:
            img_url = ""
        news["image"] = img_url
        print(f"圖片: {img_url}\n")
    print()
    news_data.append(news)

# 儲存數據
timestamp = time.strftime("%Y_%m_%d_%H_%M", time.localtime())
json_path = f"json/{timestamp}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(news_data, f, ensure_ascii=False, indent=4)

print(f"新聞資料已儲存至 {json_path}")

