import os
import json
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import time
import shutil

# --- 1. 設定資料夾路徑 ---
input_folder = "json"
output_folder = "json/processed"
move_folder = "json/Org"

os.makedirs(output_folder, exist_ok=True)
os.makedirs(move_folder, exist_ok=True)

# --- 2. 設定 Gemini API 金鑰並初始化 Client ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("請先設定你的 GEMINI_API_KEY 環境變數。")

try:
    gemini_client = genai.Client()
except Exception as e:
    raise ValueError(f"無法初始化 Gemini Client，請檢查 API 金鑰：{e}")

# --- 3. 處理資料夾內所有 JSON 檔案 ---
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"cleaned_{filename}")

        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for i, article in enumerate(data):
            print(f"➡️ 正在處理第 {i+1} 篇文章...")
            if "articles" in article:
                for j, sub_article in enumerate(article["articles"]):
                    print(f"   ➡️ 正在處理第 {j+1} 篇子文章...")

                    # (1) 去除 HTML
                    raw_content = sub_article.get("content", "")
                    soup = BeautifulSoup(raw_content, "html.parser")
                    cleaned_text = soup.get_text(separator="\n", strip=True)

                    # (2) 使用 Gemini API 去除雜訊
                    prompt = f"""
                    請去除以下文章中的雜訊，例如多餘的標題、時間戳記、來源資訊等，並最大量的保留所有新聞內容：

                    {cleaned_text}

                    你只需要回覆經過處理的內容，不需要任何其他說明或標題。
                    如果沒有文章內容，請回覆 "[清洗失敗]"。
                    """
                    
                    max_retries = 3  # 設定最大重試次數
                    retries = 0
                    success = False
                    
                    while not success and retries < max_retries:
                        try:
                            # 統一使用 client 的 generate_content 方法
                            response = gemini_client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=prompt
                            )
                            # 獲取回覆內容的方式
                            sub_article["content"] = response.candidates[0].content.parts[0].text.strip()
                            success = True  # 請求成功，跳出迴圈
                            time.sleep(1) # 成功後還是禮貌性地稍等一下
                        except Exception as e:
                            if "503 UNAVAILABLE" in str(e):
                                retries += 1
                                print(f"⚠️ 偵測到模型過載，正在嘗試第 {retries} 次重試...")
                                time.sleep(3 * retries) # 每次重試等待更久
                            else:
                                print(f"❌ 發生錯誤於文章：{filename}，錯誤訊息：{e}")
                                sub_article["content"] = "[清洗失敗]"
                                break # 其他錯誤直接跳出
                    
                    if not success:
                        print(f"❌ 嘗試 {max_retries} 次後仍無法成功處理文章：{filename}")
                        sub_article["content"] = "[清洗失敗]"


        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        shutil.move(input_file_path, os.path.join(move_folder, filename))
        print(f"✅ {filename} 處理完成！已儲存至 {output_file_path} 並移動原始檔案。")

print("🎉 所有 JSON 檔案處理完成！")