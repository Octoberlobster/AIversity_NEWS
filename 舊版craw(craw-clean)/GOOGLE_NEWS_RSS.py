import feedparser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# 初始化
rss_url = "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
feed = feedparser.parse(rss_url)

# Selenium 設定
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 可加上 headless 模式
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 儲存所有新聞的結果
all_news = []

for entry in feed.entries[:3]:  # 只抓前 3 則
    news_item = {
        "title": entry.title,
        "link": entry.link,
        "articles": []
    }

    soup = BeautifulSoup(entry.description, "html.parser")
    links = soup.find_all("a")

    for a in links:
        href = a.get("href")
        text = a.get_text(strip=True)

        # 使用 Selenium 開啟實際新聞頁面
        driver.get(href)
        time.sleep(3)  # 等待頁面載入
        html = driver.page_source
        article_soup = BeautifulSoup(html, "html.parser")
        content = article_soup.body.get_text(strip=True) if article_soup.body else "無內容"

        # 加入單篇文章資料
        news_item["articles"].append({
            "href": href,
            "text": text,
            "content": content
        })

    # 儲存該則新聞
    all_news.append(news_item)

# 關閉瀏覽器
driver.quit()

# 存成 JSON 檔案
with open("google_news_output.json", "w", encoding="utf-8") as f:
    json.dump(all_news, f, ensure_ascii=False, indent=2)

print("✅ 已儲存為 google_news_output.json")
