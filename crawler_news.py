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
# import absl.logging

# absl.logging.set_verbosity(absl.logging.ERROR)
grpc.Channel._Rendezvous = None  # 強制關閉 gRPC 連線

# 設定 API 金鑰
api_key = os.environ["GEMINI_API_KEY"] = ""
if not api_key:
    raise ValueError("請設定 GEMINI_API_KEY 環境變數")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

def extract_publish_date(text):
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36"}

    # 取前 5000 字元來限制請求回應的長度
    content = text[:5000]

    # 使用模型生成內容
    try:
        taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
        formatted_time = time.strftime("%Y/%m/%d", taiwan_time)
        response2 = model.generate_content(
            content + " 根據以上新聞摘要，請提取發布時間，格式為 yyyy/MM/dd，若僅有hours ago，則用" + formatted_time + "。",
            # generation_config=generation_config
        )
        return response2.text.strip()
    except Exception as e:
        return f"生成內容錯誤: {e}"


def crawl_news(query):
    # Google Custom Search API 設定
    API_KEY = ""  # 替換為你的 API 金鑰
    CX = ""  # 替換為你的搜尋引擎 ID
    # QUERY = [台灣 國際 政治 娛樂新聞 體育新聞 商業新聞 科技新聞 醫療保健新聞 科學新聞 教育新聞 生活品味新聞]       # 搜尋關鍵字

    # 設定請求 URL
    url = "https://www.googleapis.com/customsearch/v1"
    
    # 提取新聞標題、URL 和內容
    news_data = []
    
    for start in range(1, 11, 10):  # 每次取 10 筆，最多 100 筆
        # 設定請求參數
        params = {
            "key": API_KEY,
            "cx": CX,
            "q": query,
            "sort": "date",  # 按發布時間排序
            "dateRestrict": "h1",  # 限制 1 小時內的新聞
            "nums": 20,  # 取得 20 筆新聞
            "start": start  # 從第 1 筆開始 
        }

        # 發送請求
        response = requests.get(url, params=params)
        # 處理響應
        if response.status_code == 200:
            data = response.json()
            data2 = json.dumps(data, ensure_ascii=False, indent=4)
            with open("1.json", "w", encoding="utf-8") as f:
                f.write(data2)

            if "items" in data:
                for item in data["items"]:
                    # print(item)
                    print(f"標題: {item['title']}")
                    print(f"連結: {item['link']}")
                    snippet = item.get("snippet")
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
                        news_response.encoding = "utf-8"  # 自動檢測正確編碼
                        if news_response.status_code == 200:
                            html_source = news_response.text  # 取得網頁原始碼

                            # 使用 gemini 解析 HTML 內容
                            # response2 = model.generate_content(
                            #     html_source + " 根據以上新聞網頁，請提取主要新聞原始內容，不須整理格式。",
                            # )
                            content_str = html_source
                            # content_str = response2.text.strip()
                            print(f"內容: {content_str}")
                            # soup = BeautifulSoup(news_response.text, 'html.parser')

                            # 假設發布時間在 <time> 標籤中
                            # published_time = soup.find('time')
                            # # 如果找到了時間標籤
                            # if published_time:
                            #     print(f"發布時間: {published_time.get_text()}")
                            # else:
                            #     print("無發布時間標籤。")

                            # 根據新聞網站的 HTML 結構提取內文
                            # paragraphs = soup.find_all('p')
                            # content = []
                            # content.append("")
                            # for p in paragraphs:
                            #     text = p.get_text(strip=True)
                            #     # 停止提取內容的條件
                            #     if "延伸閱讀" in text or "責任編輯" in text or "核稿編輯" in text:
                            #         break
                            #     content.append(text)

                            # # 將段落內容合併為一個字串
                            # content_str = " ".join(content)
                            # print(f"完整內容: {content_str[:500]}...")  # 截取部分內容避免過長
                        else:
                            print("無法訪問新聞內文。")
                    except Exception as e:
                        print(f"提取內文時出錯: {e}")

                    # 儲存數據
                    news_data.append({
                        "Title": item['title'],
                        "URL": item['link'],
                        "Content": content_str,
                        "date": published_date 
                    })

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
    with open("{}_{}.json".format(i, formatted_time), "w", encoding="utf-8") as f:
        f.write(json_data)

    return df

# 測試
news_data = ["台灣新聞", "國際新聞", "政治新聞", "娛樂新聞", "體育新聞", "商業新聞", "科技新聞", "醫療保健新聞", "科學新聞", "教育新聞", "生活品味新聞"]       # 搜尋關鍵字
for i in news_data:
    crawl_news(i)
