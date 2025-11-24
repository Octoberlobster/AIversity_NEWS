import os
from dotenv import load_dotenv
from google import genai

# 載入 .env
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("找不到 GEMINI_API_KEY，請檢查 .env")
    exit()

client = genai.Client(api_key=api_key)

print("=== 正在查詢您的 API Key 可用的模型列表 ===")
print(f"API Key 前四碼: {api_key[:4]}****")

try:
    # 列出所有模型
    count = 0
    for model in client.models.list():
        # 我們只關心支援 'generateImages' 的模型
        if "generateImages" in (model.supported_actions or []):
            print(f"\n✅ [圖片生成模型] 找到可用 ID: {model.name}")
            print(f"   支援功能: {model.supported_actions}")
            count += 1
        # 順便印出 Gemini 相關的，確認連線正常
        elif "gemini" in model.name and "generateContent" in (model.supported_actions or []):
            # 為了版面整潔，這裡只印出少數幾個代表性的文字模型
            if "flash" in model.name and count == 0: 
                print(f"ℹ️ (文字模型範例): {model.name}")

    if count == 0:
        print("\n❌ 警告：您的 API Key 權限列表中，沒有發現任何支援 'generateImages' 的模型。")
        print("原因可能是：")
        print("1. 您的 Google Cloud 專案未開通 Imagen 權限（需至 Google Cloud Console 啟用 API）。")
        print("2. 您使用的是免費版 API Key，而該地區尚未開放圖片生成功能。")
        print("3. 您需要將專案連結至 Billing Account (付費帳戶) 才能使用 Imagen。")
    else:
        print(f"\n總共找到 {count} 個圖片生成模型。請將上面的 ID 填入您的程式碼中。")

except Exception as e:
    print(f"\n查詢失敗，錯誤訊息: {e}")