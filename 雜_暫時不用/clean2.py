from readability import Document
import requests
from bs4 import BeautifulSoup
import json
import os

input_file_path = "udn_data.json"
# 讀取 JSON 檔案
with open(input_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for i in range(len(data)):
    print(f"➡️ 正在處理第 {i+1} 篇文章... ({input_file_path})")
    article = data[i]

    url = article["url"]
    res = requests.get(url)
    doc = Document(res.text)
    html = doc.summary()  # 這是去雜訊後的 HTML 主內容

    soup = BeautifulSoup(html, 'html.parser')
    # print(soup.get_text(strip=True, separator="\n"))

    text = soup.get_text(strip=True, separator="\n")
    print(text)

