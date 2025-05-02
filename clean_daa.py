import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
import shutil

# === 1. 設定資料夾路徑 ===
input_folder = "json"
output_folder = "json/processed"
move_folder = "json/Org"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)
os.makedirs(move_folder, exist_ok=True)  # ✅ 確保移動資料夾存在

# === 2. 設定 Gemini API 金鑰 ===
api_key = ""
if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

def normalize_time(t):
    """將時間格式化為 YYYY/MM/DD"""
    # 提取時間 及 清除雜訊
    # 使用模型生成內容
    # taiwan_time = time.localtime()  # 取得本地時間（依據系統時區）
    # formatted_time = time.strftime("%Y/%m/%d", taiwan_time)
    # try:
        # 解析 HTML
        #     soup = BeautifulSoup(article["content"], "html.parser")
        #     # 找出 JSON-LD script
            #     ld_json_tag = soup.find("script", type="application/ld+json")
            #     # 解析 JSON 字串
            #     data = json.loads(ld_json_tag.string)
            #     # 取得 datePublished
            #     date_published = data.get("datePublished", None)
            #     if date_published:
            #         article["date"] = date_published  # 更新文章時間
            #     # else:
            #     #     article["time"] = formatted_time  # 如果沒有時間，使用當前時間
            # except:
            #     response2 = model.generate_content(
            #         article["content"] + " 根據以上新聞，請提取發布時間，如有更新時間，請提取更新時間，格式為 yyyy-mm-dd hh:mm:ss，若僅有hours ago，則用" + formatted_time + "。" +
            #         "如果沒有時間，請回覆「無法提取發布時間」" +
            #         "如果只有 月/日，請在前面加上當前年份" +
            #         "無需任何其他說明或標題。"
            #     )
            #     article["date"] = response2.text.strip()  # 更新文章時間
    return t.strftime("%Y/%m/%d")

# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"cleaned_{filename}")

        # 讀取 JSON 檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 處理每篇新聞內容
        for i, article in enumerate(data):
            print(f"➡️ 正在處理第 {i+1} 篇文章... ({filename})")

            if "content" in article:
                # (1) 去除 HTML
                soup = BeautifulSoup(article["content"], "html.parser")
                cleaned_text = soup.get_text(separator="\n", strip=True)

                # (2) 使用 Gemini API 去除雜訊
                prompt = f"""
                請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                {cleaned_text}

                你只需要回覆經過處理的內容，不需要任何其他說明或標題。
                """
                try:
                    response = model.generate_content(prompt)
                    article["content"] = response.text.strip()
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ 發生錯誤於文章：{filename}，錯誤訊息：{e}")
                    article["content"] = "[清洗失敗]"

        # 輸出處理後的結果到新 JSON 檔案
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # ✅ 將原始檔案移動到 move_folder
        shutil.move(input_file_path, os.path.join(move_folder, filename))
        print(f"✅ {filename} 處理完成！已儲存至 {output_file_path} 並移動原始檔案。")

print("🎉 所有 JSON 檔案處理完成！")