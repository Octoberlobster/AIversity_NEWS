"""
詞彙解釋模組使用範例
"""

from word_explainer import WordExplainer, explain_words, explain_from_file

def example_1_basic_usage():
    """範例 1: 基本使用方式"""
    print("=== 範例 1: 基本使用方式 ===")
    
    try:
        # 直接解釋單個詞彙
        result = explain_words("人工智慧")
        print("解釋結果:", result)
        
    except Exception as e:
        print(f"錯誤: {e}")

def example_2_multiple_words():
    """範例 2: 解釋多個詞彙"""
    print("\n=== 範例 2: 解釋多個詞彙 ===")
    
    try:
        # 解釋多個詞彙
        words = ["機器學習", "深度學習", "神經網路"]
        result = explain_words(words)
        
        # 儲存結果
        WordExplainer.save_to_file(result, "example_output.json")
        
    except Exception as e:
        print(f"錯誤: {e}")

def example_3_class_usage():
    """範例 3: 使用類別方式"""
    print("\n=== 範例 3: 使用類別方式 ===")
    
    try:
        # 創建解釋器實例
        explainer = WordExplainer()
        
        # 解釋詞彙
        result = explainer.explain_words(["區塊鏈", "加密貨幣"], delay=0.5, verbose=True)
        
        # 檢查結果
        if result.get('terms'):
            print(f"成功解釋了 {len(result['terms'])} 個詞彙")
            for term in result['terms']:
                print(f"- {term['term']}: {term['definition'][:50]}...")
        
    except Exception as e:
        print(f"錯誤: {e}")

def example_4_from_file():
    """範例 4: 從檔案讀取"""
    print("\n=== 範例 4: 從檔案讀取 ===")
    
    try:
        # 創建範例輸入檔案
        sample_words = ["量子計算", "雲端運算"]
        WordExplainer.create_sample_input(sample_words, "example_input.json")
        
        # 從檔案解釋詞彙
        result = explain_from_file("example_input.json", "example_output_from_file.json")
        
        if result.get('terms'):
            print(f"從檔案處理完成，共解釋了 {len(result['terms'])} 個詞彙")
        
    except Exception as e:
        print(f"錯誤: {e}")

def example_5_custom_api_key():
    """範例 5: 自定義 API 金鑰"""
    print("\n=== 範例 5: 自定義 API 金鑰 ===")
    
    try:
        # 使用自定義 API 金鑰（這裡只是示範，實際使用時請提供真實的金鑰）
        # explainer = WordExplainer(api_key="your_custom_api_key_here")
        # result = explainer.explain_words("自然語言處理")
        
        print("這個範例需要提供實際的 API 金鑰才能執行")
        
    except Exception as e:
        print(f"錯誤: {e}")

def mock_example():
    """模擬範例（不需要 API）"""
    print("\n=== 模擬範例（不需要 API）===")
    
    # 創建模擬資料
    mock_result = {
        "terms": [
            {
                "term": "範例詞彙",
                "definition": "（示例）這是一個範例詞彙的定義。",
                "examples": [
                    {
                        "title": "應用例子",
                        "text": "這是第一個應用範例。\n\n這是第二個應用範例。"
                    }
                ]
            }
        ]
    }
    
    # 儲存模擬結果
    WordExplainer.save_to_file(mock_result, "mock_output.json")
    print("模擬資料已儲存")

if __name__ == "__main__":
    print("詞彙解釋模組使用範例")
    print("=" * 50)
    
    # 執行模擬範例（不需要 API）
    mock_example()
    
    # 如果有 API 金鑰，可以嘗試執行以下範例
    print("\n注意：以下範例需要有效的 Gemini API 金鑰才能執行")
    print("如果沒有 API 金鑰或配額不足，會顯示錯誤訊息")
    
    # 取消註解以下行來執行實際的 API 呼叫範例
    # example_1_basic_usage()
    # example_2_multiple_words()
    # example_3_class_usage()
    # example_4_from_file()
    # example_5_custom_api_key()
    
    print("\n所有範例執行完畢！")
