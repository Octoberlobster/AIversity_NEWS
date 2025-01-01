import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import clean

def crawl_news(query):

    # Google Custom Search API 設定
    API_KEY = ""  # 替換為你的 API 金鑰
    CX = ""            # 替換為你的搜尋引擎 ID
    #QUERY = "柯文哲"       # 搜尋關鍵字

    # 設定請求 URL
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
    }

    # 提取新聞標題、URL 和內容
    news_data = []

    # 發送請求
    response = requests.get(url, params=params)

    # 處理響應
    if response.status_code == 200:
        data = response.json()
        if "items" in data:
            for item in data["items"]:
                print(f"標題: {item['title']}")
                print(f"連結: {item['link']}")
                content_str = ""
                # 爬取新聞內容
                try:
                    news_response = requests.get(item['link'], headers={"User-Agent": "Mozilla/5.0"})
                    news_response.encoding = "utf-8"  # 自動檢測正確編碼
                    if news_response.status_code == 200:
                        soup = BeautifulSoup(news_response.text, 'html.parser')

                        # 假設發布時間在 <time> 標籤中
                        published_time = soup.find('time')
                        # 如果找到了時間標籤
                        if published_time:
                            print(f"發布時間: {published_time.get_text()}")
                        else:
                            print("無發布時間標籤。")

                        # 根據新聞網站的 HTML 結構提取內文
                        paragraphs = soup.find_all('p')
                        content = []
                        content.append("")
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            # 停止提取內容的條件
                            if "延伸閱讀" in text or "責任編輯" in text or "核稿編輯" in text:
                                break
                            content.append(text)

                        # 將段落內容合併為一個字串
                        content_str = " ".join(content)
                        print(f"完整內容: {content_str[:500]}...")  # 截取部分內容避免過長
                    else:
                        print("無法訪問新聞內文。")
                except Exception as e:
                    print(f"提取內文時出錯: {e}")

                # 儲存數據
                news_data.append({
                "Title": item['title'],
                "URL": item['link'],
                "Content": content
                })

                print("-" * 50)
        else:
            print("未找到相關新聞。")
    else:
        print(f"請求失敗，狀態碼: {response.status_code}")


    # 將數據轉換為 Pandas DataFrame
    df = pd.DataFrame(news_data)
    
    # # 顯示表格
    #print(df)
    
    # # 如果需要，將表格存成 CSV
    df.to_csv("news_data.csv", index=False, encoding="utf-8-sig")
    
    return clean.clean_data(df)
