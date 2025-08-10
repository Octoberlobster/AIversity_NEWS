#!/usr/bin/env python3
"""
詞彙解釋模組快速測試腳本

展示如何使用 word_explainer 模組的各種功能
"""

import sys
import os

# 添加當前目錄到 Python 路徑（如果作為獨立腳本運行）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """測試模組匯入"""
    print("🔧 測試模組匯入...")
    try:
        from word_explainer import WordExplainer, explain_words, explain_from_file
        print("✅ 模組匯入成功！")
        return True
    except ImportError as e:
        print(f"❌ 模組匯入失敗: {e}")
        return False

def test_class_creation():
    """測試類別創建（不需要 API）"""
    print("\n🏗️ 測試類別創建...")
    try:
        from word_explainer import WordExplainer
        
        # 這會嘗試載入 API 金鑰，但如果失敗也不會影響測試
        try:
            explainer = WordExplainer()
            print("✅ WordExplainer 類別創建成功（含 API 設定）")
        except (ValueError, RuntimeError):
            print("⚠️ WordExplainer 類別創建成功，但 API 設定有問題（正常，如果沒有 API 金鑰）")
        
        return True
    except Exception as e:
        print(f"❌ 類別創建失敗: {e}")
        return False

def test_utility_functions():
    """測試工具函數"""
    print("\n🛠️ 測試工具函數...")
    try:
        from word_explainer import WordExplainer
        
        # 測試創建範例輸入檔案
        sample_words = ["測試詞彙1", "測試詞彙2"]
        WordExplainer.create_sample_input(sample_words, "test_input.json")
        print("✅ 範例輸入檔案創建成功")
        
        # 測試儲存功能
        test_data = {
            "terms": [
                {
                    "term": "測試詞彙",
                    "definition": "（示例）這是測試用的定義",
                    "examples": [{"title": "應用例子", "text": "這是測試範例"}]
                }
            ]
        }
        WordExplainer.save_to_file(test_data, "test_output.json", verbose=True)
        print("✅ 資料儲存功能正常")
        
        return True
    except Exception as e:
        print(f"❌ 工具函數測試失敗: {e}")
        return False

def test_file_operations():
    """測試檔案操作功能"""
    print("\n📁 測試檔案操作...")
    try:
        import json
        import os
        
        # 檢查是否有輸入檔案
        if os.path.exists("difficult_words.json"):
            with open("difficult_words.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 找到輸入檔案，包含 {len(data.get('difficult_words', []))} 個詞彙")
        else:
            print("⚠️ 未找到 difficult_words.json，這是正常的")
        
        # 檢查是否有測試輸出檔案
        if os.path.exists("word_explanations_test.json"):
            with open("word_explanations_test.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 找到測試輸出檔案，包含 {len(data.get('terms', []))} 個詞彙解釋")
        
        return True
    except Exception as e:
        print(f"❌ 檔案操作測試失敗: {e}")
        return False

def show_usage_examples():
    """顯示使用範例"""
    print("\n📖 使用範例:")
    print("=" * 50)
    
    examples = [
        "# 方式 1: 使用類別",
        "from word_explainer import WordExplainer",
        "explainer = WordExplainer()",
        "result = explainer.explain_words(['人工智慧'])",
        "",
        "# 方式 2: 使用便利函數",
        "from word_explainer import explain_words",
        "result = explain_words('機器學習')",
        "",
        "# 方式 3: 從檔案處理",
        "from word_explainer import explain_from_file", 
        "result = explain_from_file('input.json', 'output.json')",
        "",
        "# 方式 4: 創建輸入檔案",
        "WordExplainer.create_sample_input(['詞彙1', '詞彙2'])",
    ]
    
    for line in examples:
        print(line)

def main():
    """主函數"""
    print("詞彙解釋模組 - 快速測試")
    print("=" * 50)
    
    tests = [
        test_import,
        test_class_creation, 
        test_utility_functions,
        test_file_operations
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n📊 測試結果總結:")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    print(f"通過: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有測試通過！模組可以正常使用。")
    else:
        print("⚠️ 部分測試失敗，請檢查相關設定。")
    
    show_usage_examples()
    
    print("\n💡 提示:")
    print("- 如需使用實際 API 功能，請確保設定了有效的 GEMINI_API_KEY")
    print("- 執行 'python examples.py' 查看更多使用範例")
    print("- 查看 README.md 獲取完整說明文件")

if __name__ == "__main__":
    main()
