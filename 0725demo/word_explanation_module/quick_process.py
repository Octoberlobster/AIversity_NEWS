#!/usr/bin/env python3
"""
快速文本處理腳本
用於快速處理JSON檔案並生成詞彙解釋

使用方式：
1. python quick_process.py input.json
2. python quick_process.py input.json output.json
3. 直接執行 python quick_process.py（互動模式）
"""

import sys
import os
from smart_text_processor import SmartTextProcessor

def create_sample_json():
    """創建範例JSON檔案用於測試"""
    import json
    
    sample_data = {
        "title": "人工智慧與機器學習的應用",
        "content": "深度學習是人工智慧的一個重要分支，它利用神經網路來模擬人腦的工作方式。在醫療診斷領域，卷積神經網路能夠協助醫師進行影像分析。自然語言處理技術則可以幫助電腦理解和生成人類語言。",
        "articles": [
            {
                "id": 1,
                "title": "區塊鏈技術的發展趨勢",
                "summary": "區塊鏈是一種分散式帳本技術，具有去中心化、不可篡改的特性。智能合約是區塊鏈上可自動執行的程式碼，能夠在滿足預設條件時自動執行相應的動作。"
            },
            {
                "id": 2,
                "title": "量子計算的未來展望",
                "summary": "量子計算利用量子力學的特性來處理資訊，具有指數級的計算優勢。量子糾纏和量子疊加是量子計算的核心概念。"
            }
        ],
        "metadata": {
            "author": "科技研究團隊",
            "keywords": ["人工智慧", "機器學習", "深度學習", "神經網路", "自然語言處理"],
            "category": "科技",
            "difficulty_level": "中級"
        }
    }
    
    with open("sample_tech_news.json", 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 已創建範例檔案：sample_tech_news.json")
    return "sample_tech_news.json"

def main():
    """主函數"""
    print("🚀 快速文本處理工具")
    print("=" * 40)
    
    # 解析命令列參數
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    else:
        # 互動模式
        print("請選擇操作：")
        print("1. 處理現有JSON檔案")
        print("2. 使用範例檔案進行測試")
        
        choice = input("請輸入選項 (1/2)：").strip()
        
        if choice == "2":
            input_file = create_sample_json()
            output_file = "sample_output.json"
        else:
            input_file = input("請輸入JSON檔案路徑：").strip()
            if not input_file:
                print("❌ 未提供檔案路徑")
                return
            
            output_choice = input("是否要儲存結果到檔案？(y/n)：").strip().lower()
            if output_choice == 'y':
                output_file = input("請輸入輸出檔案名稱（例如：result.json）：").strip()
                if not output_file:
                    output_file = "analysis_result.json"
            else:
                output_file = None
    
    # 檢查輸入檔案是否存在
    if not os.path.exists(input_file):
        print(f"❌ 檔案不存在：{input_file}")
        return
    
    try:
        print(f"\n🔄 開始處理檔案：{input_file}")
        
        # 創建處理器
        processor = SmartTextProcessor()
        
        # 執行處理
        result = processor.process_json_file(input_file, output_file, verbose=True)
        
        # 顯示結果
        print("\n" + "="*50)
        print("📊 處理完成！結果摘要：")
        print("="*50)
        print(f"📁 來源檔案：{result['source_file']}")
        print(f"⏰ 處理時間：{result['processing_date']}")
        print(f"📝 提取文字段數：{result['extracted_texts_count']}")
        print(f"🔤 識別困難詞彙數：{result['difficult_words_count']}")
        print(f"💡 成功解釋詞彙數：{len(result['explanations']['terms'])}")
        
        if result['difficult_words']:
            print(f"\n🧩 識別出的困難詞彙：")
            for i, word in enumerate(result['difficult_words'], 1):
                print(f"  {i}. {word}")
        
        if result['explanations']['terms']:
            print(f"\n📖 詞彙解釋範例（顯示前3個）：")
            for i, term in enumerate(result['explanations']['terms'][:3], 1):
                print(f"\n  {i}. 【{term['term']}】")
                print(f"     定義：{term['definition']}")
                example_preview = term['examples'][0]['text'][:50] + "..." if len(term['examples'][0]['text']) > 50 else term['examples'][0]['text']
                print(f"     範例：{example_preview}")
        
        if output_file:
            print(f"\n💾 完整結果已儲存至：{output_file}")
        else:
            print(f"\n💡 提示：使用 -o 參數可以將結果儲存到檔案")
        
        print("\n✨ 處理完成！")
        
    except Exception as e:
        print(f"\n❌ 處理失敗：{e}")
        print("請檢查：")
        print("1. JSON檔案格式是否正確")
        print("2. 是否設定了 GEMINI_API_KEY 環境變數")
        print("3. 網路連線是否正常")
        print("4. API 配額是否足夠")

if __name__ == "__main__":
    main()
