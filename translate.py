import os
import json
from bs4 import BeautifulSoup
from google.cloud import translate_v3 as translate
from google.oauth2 import service_account

# === 1. 設定資料夾路徑 ===
input_folder = "Graduation-Project/json/processed"
output_folder = "Graduation-Project/json/translated"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

# === 2. 手動輸入 Google Translate API 金鑰檔案路徑 ===
api_key_path = "sigma-seer-452606-t8-568af0f7d4b1.json"
project_id = "sigma-seer-452606-t8"  # ⚠️ 確保這裡填入 **你的** Google Cloud Project ID

if not os.path.exists(api_key_path):
    raise ValueError("請先設定正確的服務帳戶金鑰路徑。")

# 使用服務帳戶金鑰初始化憑證
credentials = service_account.Credentials.from_service_account_file(api_key_path)

# 設定 Google Cloud Translation API 客戶端
translate_client = translate.TranslationServiceClient(credentials=credentials)
parent = f"projects/{project_id}/locations/global"  # ✅ 修正 parent 設定

# === 3. 處理資料夾內所有 JSON 檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"translated_{filename}")

        # 讀取 JSON 檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 處理每篇新聞內容
        for article in data:
            if "Content" in article:
                # (1) 去除 HTML
                soup = BeautifulSoup(article["Content"], "html.parser")
                cleaned_text = soup.get_text(separator="\n", strip=True)

                # (2) 使用 Google Cloud Translation API 進行翻譯
                response = translate_client.translate_text(
                    parent=parent,  # ✅ 修正 parent 參數
                    contents=[cleaned_text],
                    mime_type="text/plain",  # ✅ 明確指定 MIME 類型
                    source_language_code="zh-TW",  # ✅ 設定來源語言
                    target_language_code="en"
                )

                translated_text = response.translations[0].translated_text  # 提取翻譯結果
                article["Content"] = translated_text  # 更新翻譯後的內容

        # 輸出處理後的結果到新 JSON 檔案
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"✅ {filename} 處理完成！已儲存至 {output_file_path}")

print("🎉 所有 JSON 檔案處理完成！")
