import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import types
from PIL import Image
from io import BytesIO

# 從 .env 檔案載入環境變數
load_dotenv()

# 設定 API 金鑰
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 撰寫文字提示
contents = ('請幫我生成一張 3D 渲染圖，內容是一隻戴著高帽、長著翅膀的豬，'
            '飛過一個充滿綠色植物、快樂的未來科幻城市。')

try:
    # 呼叫 API 生成內容
    # 注意：使用 genai.GenerativeModel 而不是 client.models
    model = genai.GenerativeModel('gemini-1.5-flash-preview-0514')
    response = model.generate_content(
        contents=contents,
        generation_config=types.GenerationConfig(
            response_mime_type='image/png' # 直接指定輸出圖片格式
        )
    )

    # 處理並儲存圖片
    image_data = response.candidates[0].content.parts[0].inline_data.data
    image = Image.open(BytesIO(image_data))
    image.save('generated-image.png')
    print("圖片已成功生成並儲存為 generated-image.png")
    image.show()

except Exception as e:
    print(f"發生錯誤：{e}")

