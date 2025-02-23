import json
from bs4 import BeautifulSoup
from google.colab import drive

# 🚀 掛載 Google Drive
drive.mount('/content/drive')

# 🗂 設定你的檔案路徑（請確認放在 Google Drive 對應的資料夾）
input_file_path = "/content/drive/MyDrive/台灣新聞_2025_02_24_00.json"
output_file_path = "/content/drive/MyDrive/台灣新聞_cleaned.json"

# 📂 讀取 JSON 檔案
with open(input_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 🔍 處理每篇新聞內容，去除 HTML
for article in data:
    soup = BeautifulSoup(article["Content"], "html.parser")
    article["Content"] = soup.get_text(separator="\n", strip=True)  # 轉換為純文字

# 💾 儲存乾淨的 JSON 檔案到 Google Drive
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ 處理完成！純文字新聞已儲存至 {output_file_path}")
