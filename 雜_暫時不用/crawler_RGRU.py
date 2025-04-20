# 爬取 RGRU 網頁原始碼

import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import json
import google.generativeai as genai
import os
import clean
import time
import grpc
# import absl.logging

# absl.logging.set_verbosity(absl.logging.ERROR)
grpc.Channel._Rendezvous = None  # 強制關閉 gRPC 連線

# 設定 API 金鑰
# api_key = os.environ["GEMINI_API_KEY"] = "AIzaSyDwNOkobaknphQQx8NqSVZ6bDSvW_pizlg"
# if not api_key:
#     raise ValueError("請設定 GEMINI_API_KEY 環境變數")

# genai.configure(api_key=api_key)
# model = genai.GenerativeModel('gemini-2.0-flash')

# def extract_publish_date(text):
#     # 取前 5000 字元來限制請求回應的長度
#     content = text[:5000]

#     # 使用模型生成內容
#     try:
#         taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
#         formatted_time = time.strftime("%Y/%m/%d", taiwan_time)
#         response2 = model.generate_content(
#             content + " 根據以上新聞摘要，請提取發布時間，如有更新時間，請提取更新時間，格式為 yyyy/MM/dd，若僅有hours ago，則用" + formatted_time + "。" +
#             "如果沒有時間，請回覆「無法提取發布時間」" +
#             "如果只有 月/日，請在前面加上當前年份" +
#             "無需任何其他說明或標題。"
#             # generation_config=generation_config
#         )
#         return response2.text.strip()
#     except Exception as e:
#         return f"生成內容錯誤: {e}"

def crawl_news(url):
    # 提取新聞標題、URL 和內容
    news_data = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36",
        'Referer': 'https://www.rg.ru/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url, headers=headers)
    print(f"請求狀態碼: {response.status_code}")
    # 設定請求參數
    soup = BeautifulSoup(response.text, 'html.parser')
    # 提取新聞標題、URL 和內容
    articles = soup.find_all('div', class_='PageSearchContentNews_listItem__rs_8d')
    for article in articles:
        title = article.find('span', class_='ItemOfListStandard_title__Ajjlf').text.strip()
        link = article.find('a', class_='ItemOfListStandard_datetime__GstJi')['href']
        # content = article.find('div', class_='PageSearchContentNews_listItem__description__3v6rZ').text.strip()
        published_date = article.find('a', class_='ItemOfListStandard_datetime__GstJi').text.strip()

        print(f"標題: {title}")
        print(f"連結: {link}")
        print(f"發布日期: {published_date}")

        # 儲存數據
        # news_data.append({
        #     "Title": title,
        #     "URL": link,
        #     "Content": content,
        #     "date": published_date 
        # })
    # 處理響應
    # if response.status_code == 200:
    #     data = response.json()
    #     data2 = json.dumps(data, ensure_ascii=False, indent=4)
    #     with open("1.json", "w", encoding="utf-8") as f:
    #         f.write(data2)

    #         if "items" in data:
    #             for item in data["items"]:
    #                 if("|" in item["title"] or "標籤" in item["title"] or "在线" in item["title"] or "直播" in item["title"] or "中西區-府城之心" in item["title"] or '专题' in item["title"] or '百科' in item["title"] or 'facebook' in item["link"] or "youtube" in item["title"] or 'twitter' in item["link"] or 'instagram' in item["link"] or 'tiktok' in item["link"] or 'linkedin' in item["link"] or 'pinterest' in item["link"] or 'reddit' in item["link"]):
    #                     continue    # 過濾掉標題中包含 "|" 或 "標籤" 的新聞
    #                 # print(item)
    #                 print(f"標題: {item['title']}")
    #                 print(f"連結: {item['link']}")
    #                 # snippet = item.get("snippet")
    #                 # print(f"摘要: {snippet}")
    #                 content_str = ""

    #                 # 爬取新聞內容
    #                 try:
    #                     headers = {
    #                         "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
    #                     }
    #                     news_response = requests.get(item['link'], headers=headers)
    #                     news_response.encoding = "utf-8"  # 自動檢測正確編碼
    #                     if news_response.status_code == 200:
    #                         html_source = news_response.text  # 取得網頁原始碼
    #                         content_str = html_source
    #                         published_date = extract_publish_date(content_str)
    #                         print(f"發布日期: {published_date}")    
    #                         print(f"內容: {content_str}")
    #                     else:
    #                         print("無法訪問新聞內文。")
    #                 except Exception as e:
    #                     print(f"提取內文時出錯: {e}")

    #                 # 儲存數據
    #                 news_data.append({
    #                     "Title": item['title'],
    #                     "URL": item['link'],
    #                     "Content": content_str,
    #                     "date": published_date 
    #                 })

    #                 print("-" * 50)
    #         else:
    #             print("未找到相關新聞。")
    #     else:
    #         print(f"請求失敗，狀態碼: {response.status_code}")

    # 將數據轉換為 Pandas DataFrame
    # df = pd.DataFrame(news_data)

    # # 轉換為 JSON 格式
    # json_data = df.to_json(orient="records", force_ascii=False, indent=4)

    # # 輸出 JSON
    # print(json_data)

    # taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
    # formatted_time = time.strftime("%Y_%m_%d", taiwan_time)
    # with open("{}_{}.json".format(i, formatted_time), "w", encoding="utf-8") as f:
    #     f.write(json_data)

    # return df

# 測試
url = "https://www.rg.ru/search?text=%25D0%2592%25D0%25A1%25D0%25A3&sort=relevance&datefrom=1740326400&dateto=1743091200"
crawl_news(url)