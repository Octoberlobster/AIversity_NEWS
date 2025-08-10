#!/usr/bin/env python3
"""
智能文本處理演示腳本
展示如何從JSON中提取內容並識別困難詞彙（模擬版本）
"""

import json
import re
from typing import List, Dict, Set

class DemoTextAnalyzer:
    """演示版文本分析器"""
    
    def __init__(self):
        self.stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個',
            '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好',
            '自己', '這', '還', '可以', '出', '來', '他', '她', '它', '這個', '那個', '因為',
            '所以', '但是', '然後', '如果', '這樣', '那樣', '什麼', '怎麼', '為什麼',
            '等', '等等', '以及', '並且', '或者', '而且', '可能', '應該', '必須',
            '已經', '還是', '或是', '否則', '雖然', '不過', '只是', '而已',
            '、', '，', '。', '？', '！', '：', '；', '"', '"', ''', ''', '（', '）'
        }
    
    def extract_text_from_json(self, json_data) -> List[str]:
        """從JSON中提取文字"""
        texts = []
        
        def _extract(data):
            if isinstance(data, str):
                cleaned = self._clean_text(data)
                if cleaned and len(cleaned) > 2:
                    texts.append(cleaned)
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(key, str):
                        cleaned_key = self._clean_text(key)
                        if cleaned_key and len(cleaned_key) > 1:
                            texts.append(cleaned_key)
                    _extract(value)
            elif isinstance(data, list):
                for item in data:
                    _extract(item)
        
        _extract(json_data)
        return texts
    
    def _clean_text(self, text: str) -> str:
        """清理文字"""
        if not text:
            return ""
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 過濾純數字或純英文
        if re.match(r'^[0-9\s\-\.]+$', text) or re.match(r'^[a-zA-Z\s]+$', text):
            return ""
        
        return text
    
    def identify_difficult_words_demo(self, texts: List[str]) -> List[str]:
        """模擬識別困難詞彙"""
        # 預定義的困難詞彙模式
        tech_terms = [
            '人工智慧', '機器學習', '深度學習', '神經網路', '自然語言處理',
            '區塊鏈', '智能合約', '分散式帳本', '去中心化', '量子計算',
            '量子糾纏', '量子疊加', '卷積神經網路', '醫療診斷', '影像分析'
        ]
        
        combined_text = " ".join(texts)
        found_words = []
        
        for term in tech_terms:
            if term in combined_text and term not in found_words:
                found_words.append(term)
        
        return found_words
    
    def generate_demo_explanations(self, words: List[str]) -> Dict:
        """生成演示用的詞彙解釋"""
        explanations = {
            '人工智慧': {
                'definition': '模擬人類智能的計算機系統，能夠執行通常需要人類智能的任務。',
                'examples': '人工智慧技術被廣泛應用於自動駕駛汽車中。\n\n醫院使用人工智慧來協助診斷疾病。\n\n智能手機的語音助手就是人工智慧的應用。'
            },
            '機器學習': {
                'definition': '一種人工智慧的分支，讓計算機能夠從數據中自動學習和改進。',
                'examples': '機器學習算法可以預測股票價格趨勢。\n\n電商平台利用機器學習推薦商品給用戶。\n\n機器學習技術幫助銀行識別信用卡詐騙。'
            },
            '深度學習': {
                'definition': '基於人工神經網路的機器學習方法，能夠處理複雜的模式識別任務。',
                'examples': '深度學習在圖像識別領域取得突破性進展。\n\n語音識別系統大多採用深度學習技術。\n\n深度學習模型能夠生成逼真的人工圖像。'
            },
            '神經網路': {
                'definition': '模仿生物神經元結構的計算模型，是深度學習的基礎架構。',
                'examples': '卷積神經網路專門用於處理圖像數據。\n\n循環神經網路適合處理序列數據。\n\n神經網路需要大量數據來訓練模型。'
            },
            '區塊鏈': {
                'definition': '一種分散式數據庫技術，通過密碼學確保數據的安全性和不可篡改性。',
                'examples': '比特幣是區塊鏈技術的第一個應用。\n\n供應鏈管理可以利用區塊鏈追蹤商品來源。\n\n區塊鏈技術能夠提高金融交易的透明度。'
            },
            '量子計算': {
                'definition': '利用量子力學原理進行計算的新型計算方式，具有強大的並行處理能力。',
                'examples': '量子計算機能夠快速破解傳統加密算法。\n\n製藥公司使用量子計算來模擬分子結構。\n\n量子計算在優化問題上具有巨大優勢。'
            }
        }
        
        terms_list = []
        for word in words:
            if word in explanations:
                exp = explanations[word]
                term_data = {
                    "term": word,
                    "definition": f"（示例）{exp['definition']}",
                    "examples": [
                        {
                            "title": "應用例子",
                            "text": exp['examples']
                        }
                    ]
                }
                terms_list.append(term_data)
        
        return {"terms": terms_list}

def demo_process_json(json_file: str):
    """演示處理JSON檔案的流程"""
    print(f"🚀 開始演示處理：{json_file}")
    print("=" * 50)
    
    # 步驟1：讀取JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ JSON檔案讀取成功")
    except Exception as e:
        print(f"❌ 讀取失敗：{e}")
        return
    
    # 步驟2：創建分析器
    analyzer = DemoTextAnalyzer()
    
    # 步驟3：提取文字
    print("\n🔍 正在提取文字內容...")
    texts = analyzer.extract_text_from_json(data)
    print(f"✅ 已提取 {len(texts)} 段文字內容")
    
    print("\n📝 提取的文字內容樣本：")
    for i, text in enumerate(texts[:5], 1):
        print(f"  {i}. {text[:60]}{'...' if len(text) > 60 else ''}")
    
    # 步驟4：識別困難詞彙
    print("\n🧠 正在識別困難詞彙...")
    difficult_words = analyzer.identify_difficult_words_demo(texts)
    print(f"✅ 識別出 {len(difficult_words)} 個困難詞彙")
    
    print("\n🔤 困難詞彙列表：")
    for i, word in enumerate(difficult_words, 1):
        print(f"  {i}. {word}")
    
    # 步驟5：生成解釋
    print("\n📖 正在生成詞彙解釋...")
    explanations = analyzer.generate_demo_explanations(difficult_words)
    print(f"✅ 成功生成 {len(explanations['terms'])} 個詞彙解釋")
    
    # 步驟6：顯示結果
    print("\n" + "=" * 50)
    print("📊 處理完成！詞彙解釋結果：")
    print("=" * 50)
    
    for term in explanations['terms']:
        print(f"\n📚 【{term['term']}】")
        print(f"定義：{term['definition']}")
        print("範例：")
        examples = term['examples'][0]['text'].split('\n\n')
        for i, example in enumerate(examples, 1):
            if example.strip():
                print(f"  {i}. {example.strip()}")
    
    # 步驟7：儲存結果
    output_file = "demo_result.json"
    final_result = {
        "source_file": json_file,
        "extracted_texts_count": len(texts),
        "difficult_words_count": len(difficult_words),
        "difficult_words": difficult_words,
        "explanations": explanations
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果已儲存至：{output_file}")
    print("\n🎉 演示完成！")

def main():
    """主函數"""
    print("📖 智能文本處理演示程式")
    print("此版本不需要API金鑰，使用預設的詞彙識別和解釋")
    print("=" * 60)
    
    # 檢查是否有範例檔案
    sample_file = "sample_tech_news.json"
    if not os.path.exists(sample_file):
        print("⚠️ 未找到範例檔案，正在創建...")
        # 重新創建範例檔案
        sample_data = {
            "title": "人工智慧與機器學習的應用",
            "content": "深度學習是人工智慧的一個重要分支，它利用神經網路來模擬人腦的工作方式。在醫療診斷領域，卷積神經網路能夠協助醫師進行影像分析。自然語言處理技術則可以幫助電腦理解和生成人類語言。",
            "articles": [
                {
                    "title": "區塊鏈技術的發展趨勢",
                    "summary": "區塊鏈是一種分散式帳本技術，具有去中心化、不可篡改的特性。智能合約是區塊鏈上可自動執行的程式碼。"
                },
                {
                    "title": "量子計算的未來展望", 
                    "summary": "量子計算利用量子力學的特性來處理資訊，量子糾纏和量子疊加是量子計算的核心概念。"
                }
            ]
        }
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已創建範例檔案：{sample_file}")
    
    # 執行演示
    demo_process_json(sample_file)

if __name__ == "__main__":
    import os
    main()
