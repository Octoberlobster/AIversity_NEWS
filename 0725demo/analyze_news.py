import json
import os
import google.generativeai as genai
from dotenv import load_dotenv  # 匯入 dotenv 函式庫

def setup_environment_and_model():
    """載入環境變數並初始化 Gemini 模型"""
    # --- 1. 環境設定 (依照您的要求修改) ---
    # 載入 .env 檔案中的環境變數
    load_dotenv()

    # 從環境變數讀取 GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")

    # 檢查金鑰是否存在
    if not api_key:
        print("錯誤：讀取失敗，請確認 .env 檔案中已設定 GEMINI_API_KEY")
        return None

    # 初始化 Gemini 模型客戶端
    try:
        genai.configure(api_key=api_key)
        # 使用您指定的 'gemini-1.5-pro' 模型
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print("Gemini API 金鑰與模型初始化成功。")
        return model
    except Exception as e:
        print(f"初始化 Gemini 時發生錯誤: {e}")
        return None

def read_json_file(filename):
    """讀取 JSON 檔案並回傳其內容。"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{filename}'。")
        return None
    except json.JSONDecodeError:
        print(f"錯誤：檔案 '{filename}' 的 JSON 格式無效。")
        return None

def extract_difficult_words_with_gemini(model, text_content):
    """使用 Gemini API 從文本中提取較難的詞彙。"""
    # 設計給模型的指令 (Prompt)
    prompt = f"""
    你是一位語言學家。請從以下這段台灣新聞內文中，挑選出對於一般大眾可能比較專業或不熟悉的詞彙。
    請只用一個 JSON 格式的陣列（list of strings）回傳這些詞彙，不要包含任何說明文字或 markdown 標籤。

    新聞內文：
    ---
    {text_content}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        # 直接解析 JSON 字串
        difficult_words = json.loads(response.text)
        return difficult_words
    except json.JSONDecodeError:
        print("錯誤：無法解析 Gemini API 的回覆。")
        print("Gemini 的原始回覆內容：\n", response.text)
        return None
    except Exception as e:
        print(f"呼叫 Gemini API 時發生錯誤：{e}")
        return None

def save_to_json(data, filename):
    """將資料儲存為 JSON 檔案。"""
    output_data = {"difficult_words": data}
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"分析完成！成功將困難詞彙儲存至 '{filename}'")

# --- 主程式執行區塊 ---
def main():
    input_filename = '0725demo\\news.json'
    output_filename = '0725demo\difficult_words.json'

    # 1. 設定環境與模型
    model = setup_environment_and_model()
    if not model:
        return  # 如果設定失敗，則終止程式

    # 2. 讀取原始新聞 JSON 檔案
    news_data = read_json_file(input_filename)
    if not news_data or 'content' not in news_data:
        print("新聞檔案讀取失敗，或缺少 'content' 欄位。")
        return

    # 3. 呼叫 Gemini API 提取詞彙
    print("正在分析新聞內容，請稍候...")
    words = extract_difficult_words_with_gemini(model, news_data['content'])
    
    # 4. 儲存結果
    if words:
        save_to_json(words, output_filename)

if __name__ == "__main__":
    main()
