import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

def setup_environment_and_model():
    """載入環境變數並初始化 Gemini 模型"""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("錯誤：讀取失敗，請確認 .env 檔案中已設定 GEMINI_API_KEY")
        return None

    try:
        genai.configure(api_key=api_key)
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

def get_explanations_for_words(model, words_list):
    """使用 Gemini 為詞彙列表產生解釋和範例。"""
    terms_list = []
    
    prompt_template = """
    你是一位知識淵博的詞典編纂專家。
    針對以下提供的台灣常用詞彙，請提供約50字的「名詞解釋」和「應用範例」。
    請嚴格依照以下 JSON 格式回傳，不要包含任何 markdown 標籤或額外的說明文字。

    格式範例：
    {{
      "definition": "這裡放簡潔明瞭的名詞解釋。",
      "example_text": "這是一個應用範例。\\n\\n這是另一個應用範例。\\n\\n第三個應用範例。"
    }}

    要解釋的詞彙是：「{word}」
    
    注意：
    1. definition 應該是簡潔的定義說明
    2. example_text 應該包含2-3個應用範例，使用 \\n\\n 分隔
    3. 範例應該展示該詞彙在實際語境中的使用方式
    """

    for word in words_list:
        print(f"正在查詢詞彙：「{word}」...")
        prompt = prompt_template.format(word=word)
        
        try:
            response = model.generate_content(prompt)
            
            # 清理回應文字
            cleaned_text = response.text.strip()
            
            # 移除 Gemini 可能加入的 Markdown 標籤
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:].strip()
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3].strip()
            
            # 解析 JSON 回應
            result = json.loads(cleaned_text)
            
            # 轉換為目標格式
            term_data = {
                "term": word,
                "definition": f"（示例）{result['definition']}",
                "examples": [
                    {
                        "title": "應用例子",
                        "text": result["example_text"]
                    }
                ]
            }
            
            terms_list.append(term_data)
            time.sleep(1) 
            
        except json.JSONDecodeError:
            print(f"錯誤：即使清理過，仍然無法解析詞彙「{word}」的 API 回覆。跳過此詞彙。")
            print("清理前的原始回覆：\n", response.text)
            print("清理後的文字：\n", cleaned_text)
            continue
        except Exception as e:
            print(f"查詢詞彙「{word}」時發生錯誤：{e}。跳過此詞彙。")
            continue
            
    return {"terms": terms_list}

def save_to_json(data, filename):
    """將資料儲存為 JSON 檔案。"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n任務完成！成功將所有詞彙解釋儲存至 '{filename}'")

def main():
    # 直接使用當前目錄的檔案
    input_filename = 'difficult_words.json'
    output_filename = 'word_explanations.json'

    model = setup_environment_and_model()
    if not model:
        return

    data = read_json_file(input_filename)
    if not data or 'difficult_words' not in data or not data['difficult_words']:
        print(f"檔案 '{input_filename}' 讀取失敗，或其中不包含 'difficult_words' 列表。")
        return
        
    words_to_explain = data['difficult_words']
    
    print("\n--- 開始進行詞彙解釋 ---")
    explanations_data = get_explanations_for_words(model, words_to_explain)
    print("--- 詞彙解釋結束 ---\n")
    
    if explanations_data and explanations_data.get('terms'):
        print(f"成功解釋了 {len(explanations_data['terms'])} 個詞彙，正在存檔...")
        save_to_json(explanations_data, output_filename)
    else:
        print("錯誤：沒有成功解釋任何詞彙，因此未產生輸出檔案。")
        print("請檢查上方是否有 API 連線或資料解析的錯誤訊息。")

if __name__ == "__main__":
    main()

