import os
from io import BytesIO

from dotenv import load_dotenv  # pip install python-dotenv
from google import genai        # pip install google-genai
from google.genai import types
from PIL import Image           # pip install Pillow

def main():
    # 載入 .env，把 GEMINI_API_KEY 放入環境變數
    load_dotenv()  # 預設讀取當前目錄的 .env

    # 初始化用戶端（若未手動傳 api_key，SDK 會從環境變數讀取）
    # 亦可顯式指定：genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    client = genai.Client()

    # 提示詞：可自行修改
    prompt = (
        "Create a cinematic photo of a large building at night with a giant neon text "
        "projection mapped on the front saying 'HELLO VS CODE'. Include a brief caption."
    )

    # 呼叫圖像生成（必須包含 TEXT 與 IMAGE）
    # 注意：影像生成功能不支援僅輸出圖片，請務必設定 response_modalities=['TEXT','IMAGE']
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        ),
    )

    # 解析回應：列印文字、保存圖片
    img_idx = 1
    candidates = getattr(response, "candidates", [])
    if not candidates:
        print("No candidates returned.")
        return

    parts = getattr(candidates[0].content, "parts", [])
    if not parts:
        print("No parts in the candidate.")
        return

    for part in parts:
        # 文字段落
        if getattr(part, "text", None):
            print("Caption/Text:", part.text.strip())
        # 影像資料（inline_data.data 可能是 bytes 或 base64，SDK 會處理為 bytes）
        elif getattr(part, "inline_data", None):
            data = part.inline_data.data
            # 某些環境若為 base64 字串，可改成：
            #   from base64 import b64decode
            #   data = b64decode(data)
            image = Image.open(BytesIO(data))
            filename = f"gen_image_{img_idx}.png"
            image.save(filename)
            print(f"Saved image: {filename}")
            img_idx += 1

if __name__ == "__main__":
    main()
