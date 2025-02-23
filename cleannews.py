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


import json
from bs4 import BeautifulSoup
from google.colab import drive, userdata
import google.generativeai as genai

#  掛載 Google Drive

#  設定你的檔案路徑（請確認放在 Google Drive 對應的資料夾）
input_file_path = "/content/drive/MyDrive/台灣新聞_cleaned.json"
output_file_path = "/content/drive/MyDrive/台灣新聞_cleaned_test.json"

#  從 Google Colab userdata 取得 Gemini API 金鑰
api_key = userdata.get('GEMINI_API_KEY')  #使用你設定的密鑰名稱
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

#  讀取 JSON 檔案
with open(input_file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

#  處理每篇新聞內容，去除 HTML 和雜訊
for article in data:
    # 去除 HTML
    soup = BeautifulSoup(article["Content"], "html.parser")
    cleaned_text = soup.get_text(separator="\n", strip=True)

    # 使用 Gemini API 去除雜訊
    prompt = f"""
    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並保留主要的新聞內容：

    {cleaned_text}
    """
    response = model.generate_content(prompt)
    article["Content"] = response.text  # 更新文章內容

#  儲存乾淨的 JSON 檔案到 Google Drive
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ 處理完成！純文字新聞已儲存至 {output_file_path}")
