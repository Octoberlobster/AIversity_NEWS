# 從 新聞平台 直接爬取新聞
# 中央社: https://www.cna.com.tw/list/aall.aspx
# 篩選條件: 1 小時內的新聞
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import google.generativeai as genai
import grpc
from datetime import datetime, timedelta

grpc.Channel._Rendezvous = None  # 強制關閉 gRPC 連線

# 設定 API 金鑰
api_key = os.environ["GEMINI_API_KEY"] = "AIzaSyDvR1D_tPfP4Jv-YSdM2wckCKoVKSoJBHs"
if not api_key:
    raise ValueError("請設定 GEMINI_API_KEY 環境變數")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')


def extract_publish_date(text):
    taiwan_time = time.localtime()  # 取得本地時間
    formatted_time = time.strftime("%Y/%m/%d", taiwan_time)

    try:
        content = text[:5000]  # 限制輸入長度
        response = model.generate_content(
            content + f" 根據以上新聞摘要，請提取發布時間，格式為 yyyy/MM/dd，若僅有hours ago，則用 {formatted_time}。"
        )
        return response.text.strip()
    except Exception as e:
        return f"生成內容錯誤: {e}"


def crawl_news():
    platform_urls = ["https://www.cna.com.tw/list/aall.aspx", # 中央社
            # "https://www.googleapis.com/customsearch/v2",
            # "https://www.googleapis.com/customsearch/v3"
            ]
    news_data = []

    # 取得當前時間（yyyy_mm_dd_hh）作為資料夾名稱
    timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
    save_dir = os.path.join("json", timestamp)
    os.makedirs(save_dir, exist_ok=True)  # 建立資料夾（如果不存在）

    # 取得當前時間並計算一小時內的範圍
    current_time = datetime.now()
    one_hour_ago = current_time - timedelta(hours=1)

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
    }

    for platform_url in platform_urls:
        response = requests.get(platform_url, headers=headers)  
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            soup = soup.find("ul", id="jsMainList")            
            li_tag = soup.find_all("li")
            for item in li_tag:
                news = {}
                # print(item)

                # 取得標題與連結
                a_tag = item.find("a")

                # 取得日期並過濾一小時內的新聞
                date_tag = item.find("div", class_="date")
                if date_tag:
                    news_time_str = date_tag.text.strip()
                    news_time = datetime.strptime(news_time_str, "%Y/%m/%d %H:%M")
                            
                # print(a_tag)
                if a_tag and "news" in a_tag["href"] and news_time >= one_hour_ago:
                    # print(f"連結: https://www.cna.com.tw{a_tag['href']}")

                    news["date"] = news_time_str
                    news["url"] = "https://www.cna.com.tw" + a_tag["href"]
                    news["source"] = "中央社"
                else:
                    continue

                # 取得圖片
                try:
                    img_tag = item.find("img")
                    # print(img_tag)
                    news["image_url"] = img_tag["src"] if img_tag else "無圖片"
                except:
                    news["image_url"] = "無圖片"

                # 取得標題文字
                span_tag = item.find("span")
                news["title"] = span_tag.text.strip() if span_tag else "無標題"
                
                news_content = requests.get(news["url"], headers=headers)
                news_content.encoding = "utf-8"
                if news_content.status_code == 200:
                    soup = BeautifulSoup(news_content.text, "html.parser")
                    body_content = str(soup.body)  # 提取 <body> 內的所有 HTML 內容
                    news["content"] = body_content  # 儲存原始 HTML 內容
                else:
                    print("無法訪問新聞內文。")
                    news["content"] = "無法訪問新聞內文。"

                news_data.append(news)
                print(news)

            # else:
            #     print("未找到相關新聞。")
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")



crawl_news()