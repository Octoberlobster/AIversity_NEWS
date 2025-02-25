import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import google.generativeai as genai
import grpc

grpc.Channel._Rendezvous = None  # 強制關閉 gRPC 連線

# 設定 API 金鑰
api_key = os.environ["GEMINI_API_KEY"] = ""
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


def crawl_news(query):
    API_KEY = ""  # Google API 金鑰
    CX = ""  # Google 搜尋引擎 ID

    url = "https://www.googleapis.com/customsearch/v1"
    news_data = []

    # 取得當前時間（yyyy_mm_dd_hh）作為資料夾名稱
    timestamp = time.strftime("%Y_%m_%d_%H", time.localtime())
    save_dir = os.path.join("json", timestamp)
    os.makedirs(save_dir, exist_ok=True)  # 建立資料夾（如果不存在）

    for start in range(1, 11, 10):  # 取 10 筆，最多 100 筆
        params = {
            "key": API_KEY,
            "cx": CX,
            "q": query,
            "sort": "date",
            "dateRestrict": "h1",
            "num": 10,  # 每次最多 10 筆
            "start": start
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            
            if "items" in data:
                for item in data["items"]:
                    print(f"標題: {item['title']}")
                    print(f"連結: {item['link']}")
                    snippet = item.get("snippet", "")
                    published_date = extract_publish_date(snippet)
                    print(f"發布日期: {published_date}")
                    print(f"摘要: {snippet}")

                    content_str = ""

                    # 爬取新聞內容
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
                        }
                        news_response = requests.get(item['link'], headers=headers)
                        news_response.encoding = "utf-8"

                        if news_response.status_code == 200:
                            content_str = news_response.text  # 儲存原始 HTML 內容
                        else:
                            print("無法訪問新聞內文。")
                    except Exception as e:
                        print(f"提取內文時出錯: {e}")

                    # 儲存數據
                    news_data.append({
                        "Title": item['title'],
                        "URL": item['link'],
                        "Content": content_str,
                        "Date": published_date
                    })

                    print("-" * 50)
            else:
                print("未找到相關新聞。")
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")

    # 儲存 JSON 檔案
    json_filename = f"{query}_{timestamp}.json"
    json_path = os.path.join(save_dir, json_filename)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)

    print(f"新聞已儲存至: {json_path}")
    return news_data


# 測試
news_categories = ["台灣新聞", "國際新聞", "政治新聞", "娛樂新聞", "體育新聞", "商業新聞", "科技新聞", "醫療保健新聞", "科學新聞", "教育新聞", "生活品味新聞"]

for category in news_categories:
    crawl_news(category)
