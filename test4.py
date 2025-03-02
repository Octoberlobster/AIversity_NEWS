import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime, timedelta

def fetch_cna_news():
    url = "https://www.cna.com.tw/list/aall.aspx"
    return fetch_news(url, "cna")

def fetch_tvbs_news():
    url = "https://news.tvbs.com.tw/realtime"
    return fetch_news(url, "tvbs")

# def fetch_ftv_news():
#     url = "https://www.ftvnews.com.tw/realtime/"
#     return fetch_news(url, "ftv")

def fetch_news(url, source):
    news_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"請求 {source} 失敗，狀態碼: {response.status_code}")
        return news_data

    soup = BeautifulSoup(response.text, "html.parser")
    news_items = soup.find_all("li")
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)

    for item in news_items:
        news = {}
        
        a_tag = item.find("a")
        if a_tag and "href" in a_tag.attrs:
            news["url"] = a_tag["href"] if a_tag["href"].startswith("http") else url + a_tag["href"]
        else:
            continue
        
        img_tag = item.find("img")
        news["image_url"] = img_tag["src"] if img_tag and img_tag.has_attr("src") else "無圖片"
        
        span_tag = item.find("span")
        news["title"] = span_tag.text.strip() if span_tag else "無標題"
        
        date_tag = item.find("div", class_="date")
        if date_tag:
            news_time_str = date_tag.text.strip()
            try:
                news_time = datetime.strptime(news_time_str, "%Y/%m/%d %H:%M")
                if news_time >= one_hour_ago:
                    news["date"] = news_time_str
                    news_data.append(news)
                    print(news)
            except ValueError:
                continue
    
    return news_data

def crawl_news():
    all_news = fetch_cna_news() + fetch_tvbs_news() 
    
    timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
    save_dir = os.path.join("json", timestamp)
    os.makedirs(save_dir, exist_ok=True)
    json_path = os.path.join(save_dir, "news.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        import json
        json.dump(all_news, f, ensure_ascii=False, indent=4)
    
    print(f"新聞資料已儲存至 {json_path}")

crawl_news()
