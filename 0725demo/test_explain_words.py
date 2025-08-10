import json
import time

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

def get_explanations_for_words_mock(words_list):
    """模擬 Gemini API 回應的詞彙解釋功能"""
    terms_list = []
    
    # 模擬的回應資料
    mock_responses = {
        "三級三審": {
            "definition": "臺灣刑事訴訟的三個審級：地方法院、高等法院、最高法院。每級法院都有機會進行審理，確保司法程序的公正性與完整性。",
            "example_text": "這起殺人案因為案情複雜，經過三級三審，歷時多年才最終定讞。\n\n由於證據不足，高等法院發回更審，這個案件可能要走完三級三審的程序。\n\n律師建議當事人要有耐心，因為三級三審制度可以充分保障被告的權益。"
        },
        "IRB": {
            "definition": "研究倫理審查委員會（Institutional Review Board），用於審查涉及人類受試者的研究以確保倫理與安全。",
            "example_text": "這個研究計畫必須先通過 IRB 審查才能開始執行。\n\n因為 IRB 的要求，我們需要修改受試者同意書。\n\nIRB 委員仔細審閱了研究方案，並提出了一些建議。"
        }
    }

    for word in words_list:
        print(f"正在查詢詞彙：「{word}」...")
        
        if word in mock_responses:
            result = mock_responses[word]
            
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
            time.sleep(0.5)  # 模擬 API 延遲
        else:
            print(f"警告：沒有找到詞彙「{word}」的模擬資料")
            
    return {"terms": terms_list}

def save_to_json(data, filename):
    """將資料儲存為 JSON 檔案。"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n任務完成！成功將所有詞彙解釋儲存至 '{filename}'")

def main():
    # 直接使用當前目錄的檔案
    input_filename = 'difficult_words.json'
    output_filename = 'word_explanations_test.json'

    print("使用模擬模式測試程式邏輯...")

    data = read_json_file(input_filename)
    if not data or 'difficult_words' not in data or not data['difficult_words']:
        print(f"檔案 '{input_filename}' 讀取失敗，或其中不包含 'difficult_words' 列表。")
        return
        
    words_to_explain = data['difficult_words']
    print(f"成功讀取檔案 '{input_filename}'，找到 {len(words_to_explain)} 個詞彙：{words_to_explain}")
    
    print("\n--- 開始進行詞彙解釋 ---")
    explanations_data = get_explanations_for_words_mock(words_to_explain)
    print("--- 詞彙解釋結束 ---\n")
    
    if explanations_data and explanations_data.get('terms'):
        print(f"成功解釋了 {len(explanations_data['terms'])} 個詞彙，正在存檔...")
        save_to_json(explanations_data, output_filename)
    else:
        print("錯誤：沒有成功解釋任何詞彙，因此未產生輸出檔案。")

if __name__ == "__main__":
    main()
