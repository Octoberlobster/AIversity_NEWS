import google.generativeai as genai
from google.generativeai import types
from PIL import Image
from io import BytesIO
import os

# --- 設定 ---
# 建議將您的 API 金鑰設定為環境變數 GOOGLE_API_KEY
# 如果沒有設定環境變數，請取消以下註解並填入您的金鑰
# genai.configure(api_key="YOUR_API_KEY") 

def generate_image_from_text_official(prompt, output_path):
    """
    使用官方文件範例中的 client 模式，從文字提示生成圖片並儲存。

    Args:
        prompt (str): 用於生成圖片的文字提示。
        output_path (str): 圖片儲存的完整路徑 (包含檔名)。
    """
    try:
        print("正在初始化 Gemini Client...")
        # 根據您的範例，我們使用 genai.Client()
        # 它會自動尋找環境變數中的 API 金鑰
        client = genai.Client()

        print(f"正在使用提示生成圖片: '{prompt[:30]}...'")
        
        # 使用 client.models.generate_content 方法呼叫 API
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
              response_modalities=['TEXT', 'IMAGE']
            )
        )

        # 從回應中尋找並處理圖片數據
        image_data = None
        for part in response.candidates[0].content.parts:
            # 檢查 part 是否包含圖片數據 (inline_data)
            if part.inline_data:
                image_data = part.inline_data.data
                break

        if image_data:
            print(f"成功生成圖片，正在儲存至: {output_path}")
            # 將二進位數據轉換為圖片物件
            image = Image.open(BytesIO(image_data))
            
            # 儲存圖片到指定路徑
            image.save(output_path)
            print(f"圖片儲存完畢。")

            # 在互動環境中，可以直接顯示圖片 (可選)
            # image.show() 
            
        else:
            print("錯誤：API 回應中未找到有效的圖片數據。")
            # 完整印出回應，方便除錯
            print("API Response:", response)

    except Exception as e:
        print(f"生成圖片時發生錯誤: {e}")

if __name__ == "__main__":
    # 1. 準備您的新聞摘要 (建議使用英文以獲得最佳效果)
    news_summary_prompt = ('A 3D rendered image of a pig with wings '
                           'and a top hat flying over a happy, '
                           'futuristic sci-fi city with lots of greenery.')

    # 2. 設定儲存圖片的資料夾與檔名
    output_folder = "Generated_News_Images_Official"
    output_filename = "gemini_official_image.png"
    
    # 檢查並建立儲存資料夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已建立資料夾: {output_folder}")

    # 組合完整的儲存路徑
    full_path = os.path.join(output_folder, output_filename)

    # 3. 呼叫函式生成並儲存圖片
    generate_image_from_text_official(news_summary_prompt, full_path)
