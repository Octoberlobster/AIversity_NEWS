import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime, timedelta

def crawl_news():
    platform_urls = ["https://www.cna.com.tw/list/aall.aspx"]  # 中央社新聞列表
    news_data = []  # 存放新聞資料

    # 取得當前時間（yyyy_mm_dd_hh）作為資料夾名稱
    timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
    save_dir = os.path.join("json", timestamp)
    os.makedirs(save_dir, exist_ok=True)  # 建立資料夾（如果不存在）

    # 設定時間範圍（過去1小時內的新聞）
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
    }

    for platform_url in platform_urls:
        try:
            response = requests.get(platform_url, headers=headers)
            if response.status_code != 200:
                print(f"請求失敗，狀態碼: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            news_list = soup.find("ul", id="jsMainList")

            if not news_list:
                print("未找到新聞列表")
                continue

            li_tags = news_list.find_all("li")
            for item in li_tags:
                news = {}

                # 取得新聞標題與連結
                a_tag = item.find("a")
                if not a_tag or "news" not in a_tag["href"]:
                    continue  # 如果沒有新聞連結，跳過

                news["url"] = "https://www.cna.com.tw" + a_tag["href"]

                # 取得新聞時間
                date_tag = item.find("div", class_="date")
                if not date_tag:
                    continue  # 沒有日期則跳過該新聞

                news_time_str = date_tag.text.strip()
                try:
                    news_time = datetime.strptime(news_time_str, "%Y/%m/%d %H:%M")
                except ValueError:
                    print(f"無法解析時間: {news_time_str}")
                    continue

                # 過濾掉超過1小時的新聞
                if news_time < one_hour_ago:
                    continue

                news["date"] = news_time_str

                # 取得標題
                span_tag = item.find("span")
                news["title"] = span_tag.text.strip() if span_tag else "無標題"

                # 取得圖片
                img_tag = item.find("img")
                news["image_url"] = img_tag["src"] if img_tag else "無圖片"

                # 取得新聞內文
                try:
                    news_content_res = requests.get(news["url"], headers=headers)
                    news_content_res.encoding = "utf-8"
                    if news_content_res.status_code == 200:
                        soup = BeautifulSoup(news_content_res.text, "html.parser")
                        paragraphs = soup.find_all("p")  # 取得所有段落
                        news["content"] = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
                    else:
                        news["content"] = "無法訪問新聞內文。"
                except Exception as e:
                    print(f"獲取內文失敗: {e}")
                    news["content"] = "無法訪問新聞內文。"

                news["source"] = "中央社"
                news_data.append(news)
                print(news)

        except Exception as e:
            print(f"爬取新聞時發生錯誤: {e}")

    # 儲存 JSON 檔案
    json_path = os.path.join(save_dir, "news.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)

    print(f"新聞資料已儲存至 {json_path}")


# 執行爬取新聞
crawl_news()
