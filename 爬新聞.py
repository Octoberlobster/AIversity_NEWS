import requests

# 設定 News API Key 和基礎 URL
API_KEY = "自己加"
BASE_URL = "https://newsapi.org/v2/everything"

def search_news(query, language="zh", page_size=100):
    """
    搜尋相關新聞
    :param query: 搜尋關鍵字
    :param language: 搜尋語言（預設 "en" 英文）
    :param page_size: 每頁顯示的結果數量
    """
    params = {
        "q": query,           # 搜尋關鍵字
        "language": language, # 指定語言
        "pageSize": page_size, # 每頁顯示數量
        "apiKey": API_KEY     # API 金鑰
    }

    # 發送 GET 請求
    response = requests.get(BASE_URL, params=params)

    # 檢查回應
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        if articles:
            print(f"\n搜尋關鍵字: {query}")
            print(f"找到 {len(articles)} 篇相關新聞：\n")
            for i, article in enumerate(articles, start=1):
                print(f"{i}. {article['title']}")
                print(f"   - 作者: {article.get('author', '未知')}")
                print(f"   - 出處: {article['source']['name']}")
                print(f"   - 發布日期: {article['publishedAt']}")
                print(f"   - 連結: {article['url']}\n")
        else:
            print(f"沒有找到與 \"{query}\" 相關的新聞。")
    else:
        print(f"發生錯誤: {response.status_code} - {response.json().get('message')}")

# 主程式
if __name__ == "__main__":
    print("歡迎使用新聞搜尋工具！\n")
    while True:
        # 提示使用者輸入搜尋關鍵字
        keyword = input("請輸入要搜尋的新聞關鍵字 (輸入 'exit' 離開): ").strip()
        if keyword.lower() == "exit":
            print("感謝使用，再見！")
            break
        elif keyword:
            search_news(keyword)
        else:
            print("請輸入有效的關鍵字！\n")
