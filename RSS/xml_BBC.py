# BBC rss feed 半小時內新聞
# 無法取得圖片 -> JS 載入
import feedparser
import time
import datetime
import requests
from bs4 import BeautifulSoup
import json

# 取得 RSS Feed
url = "https://feeds.bbci.co.uk/news/rss.xml"
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

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    }
    content = requests.get(entry.link, headers=header)
    content.encoding = "utf-8"
    # print(f"內容: {content.text}")

    # 嘗試抓取圖片
    if content.status_code == 200:
        soup = BeautifulSoup(content.text, "html.parser")
        body_content = str(soup.body)  # 提取 <body> 內的所有 HTML 內容
        news["content"] = body_content  # 儲存原始 HTML 內容

        img_url = None
        try:
            img_tag = soup.find_all("div", class_="sc-a34861b-1 jxzoZC")
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

