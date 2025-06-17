# 串gemini版
# 用摘要找尋發布時間
# 爬取網頁原始碼

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
grpc.Channel._Rendezvous = None  # 強制關閉 gRPC 連線

# 設定 API 金鑰
api_key = os.environ["GEMINI_API_KEY"] = "AIzaSyCO8TkMAGyAlj57xMmS4ODV33nkcBhNbCc"
if not api_key:
    raise ValueError("請設定 GEMINI_API_KEY 環境變數")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

def crawl_news(query):
    # Google Custom Search API 設定
    API_KEY = "AIzaSyATeTpiILU2Adnyv_mhb7sRrqa3vnWqZSU"  # 替換為你的 API 金鑰
    CX = "77b6699da8b7f477c"  # 替換為你的搜尋引擎 ID
    # QUERY = [台灣 國際 政治 娛樂新聞 體育新聞 商業新聞 科技新聞 醫療保健新聞 科學新聞 教育新聞 生活品味新聞]       # 搜尋關鍵字

    # 設定請求 URL
    url = "https://www.googleapis.com/customsearch/v1"
    
    # 提取新聞標題、URL 和內容
    news_data = []
    
    for start in range(1, 100, 10):  # 每次取 10 筆，最多 100 筆
        # 設定請求參數
        params = {
            "key": API_KEY,
            "cx": CX,
            # "q": "war in Ukraine",
            "q": "烏俄 or 俄烏 after:2025-01-20 before:2025-05-05",
            "sort": "date",  # 按發布時間排序
            "dateRestrict": "y1",  # 限制 1 小時內的新聞
            "nums": 100,  # 取得 20 筆新聞
            "start": start  # 從第 1 筆開始 
        }

        # 發送請求
        response = requests.get(url, params=params)
        # 處理響應
        if response.status_code == 200:
            data = response.json()

            # 寫入 1.json檔 測試
            # data2 = json.dumps(data, ensure_ascii=False, indent=4)
            # with open("1.json", "w", encoding="utf-8") as f:
            #     f.write(data2)

            if "items" in data:
                index =1
                for item in data["items"]:
                    # 過濾掉標題中包含 "|" 或 "標籤" 的新聞
                    if("|" in item["title"] or "標籤" in item["title"] or "在线" in item["title"] or "直播" in item["title"] or "中西區-府城之心" in item["title"] or '专题' in item["title"] or '百科' in item["title"] or 'facebook' in item["link"] or "youtube" in item["title"] or 'twitter' in item["link"] or 'instagram' in item["link"] or 'tiktok' in item["link"] or 'linkedin' in item["link"] or 'pinterest' in item["link"] or 'reddit' in item["link"]):
                        continue    

                    # print(item)
                    print(f"標題: {item['title']}")
                    print(f"連結: {item['link']}")
                    # snippet = item.get("snippet")
                    # print(f"摘要: {snippet}")
                    content_str = ""
                    published_date = ""
                    # 爬取新聞內容
                    try:
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
                        }
                        news_response = requests.get(item['link'], headers=headers)
                        news_response.encoding = "utf-8"  # 自動檢測正確編碼
                        if news_response.status_code == 200:
                            html_source = news_response.text  # 取得網頁原始碼
                            content_str = html_source
                            
                            # 提取發布時間
                            try:
                                soup = BeautifulSoup(html_source, "html.parser")
                                # meta = soup.find("meta", attrs={"property": "article:published_time"})
                                meta = soup.find("meta", attrs={"name": "pubdate"})
                                published_date = meta["content"]
                            #     published_date = extract_publish_date(content_str)
                            except Exception as e:
                                published_date = "無法提取發布時間"
                            print(f"發布日期: {published_date}")    
                            print(f"內容: {content_str}")
                        else:
                            print("無法訪問新聞內文。")
                    except Exception as e:
                        print(f"提取內文時出錯: {e}")

                    # 儲存數據
                    news_data.append({
                        "title": item['title'],
                        "url": item['link'],
                        "content": content_str,
                        "date": published_date or "",  # 如果沒有發布日期，則設為空字串
                        # "sourceorg_id": index,             # 從 1 開始
                        "sourceorg_media": "chinatimes",  # 來源媒體名稱
                    })
                    index += 1
                    print("-" * 50)
            else:
                print("未找到相關新聞。")
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")

    # 將數據轉換為 Pandas DataFrame
    df = pd.DataFrame(news_data)

    # 轉換為 JSON 格式
    json_data = df.to_json(orient="records", force_ascii=False, indent=4)

    # 輸出 JSON
    print(json_data)

    taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
    formatted_time = time.strftime("%Y_%m_%d", taiwan_time)
    with open("./json/{}_{}_Chinatimes.json".format(i, formatted_time), "w", encoding="utf-8") as f:
        f.write(json_data)

    return df

# 測試
# news_data = ["Ukraine Russian"]       # 搜尋關鍵字
news_data = ["war in Ukraine"]
for i in news_data:
    crawl_news(i)