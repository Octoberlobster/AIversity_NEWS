"""
智能文本分析與詞彙解釋程式
從JSON檔案中提取文字、識別困難詞彙並自動生成解釋

主要功能：
1. 從JSON檔案讀取文字內容
2. 使用AI識別困難詞彙
3. 自動生成詞彙解釋
4. 輸出完整結果
"""

import json
import os
import re
import time
from typing import List, Dict, Set, Optional, Union
import google.generativeai as genai
from dotenv import load_dotenv

class TextAnalyzer:
    """文本分析器 - 用於從JSON中提取文字並識別困難詞彙"""
    
    def __init__(self):
        self.difficult_words = set()
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> Set[str]:
        """載入停用詞列表"""
        # 常見的中文停用詞
        default_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個',
            '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好',
            '自己', '這', '還', '可以', '出', '來', '他', '她', '它', '這個', '那個', '因為',
            '所以', '但是', '然後', '如果', '這樣', '那樣', '什麼', '怎麼', '為什麼',
            '等', '等等', '以及', '以及', '並且', '或者', '而且', '可能', '應該', '必須',
            '已經', '還是', '或是', '否則', '雖然', '不過', '只是', '而已', '而已',
            '、', '，', '。', '？', '！', '：', '；', '"', '"', ''', ''', '（', '）',
            '【', '】', '《', '》', '〈', '〉', '…', '——', '－', '·'
        }
        
        # 嘗試從檔案載入停用詞（如果存在）
        stopwords_file = "Stopwords-zhTW.txt"
        if os.path.exists(stopwords_file):
            try:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    file_stopwords = {line.strip() for line in f if line.strip()}
                default_stopwords.update(file_stopwords)
                print(f"已載入停用詞檔案：{stopwords_file}")
            except Exception as e:
                print(f"載入停用詞檔案失敗：{e}")
        
        return default_stopwords
    
    def extract_text_from_json(self, json_data: Union[Dict, List, str], max_depth: int = 10) -> List[str]:
        """
        從JSON資料中遞歸提取所有文字內容
        
        Args:
            json_data: JSON資料
            max_depth: 最大遞歸深度
            
        Returns:
            提取的文字列表
        """
        texts = []
        
        def _extract_recursive(data, depth=0):
            if depth > max_depth:
                return
            
            if isinstance(data, str):
                # 清理文字並添加到列表
                cleaned_text = self._clean_text(data)
                if cleaned_text and len(cleaned_text) > 2:  # 過濾太短的文字
                    texts.append(cleaned_text)
            
            elif isinstance(data, dict):
                for key, value in data.items():
                    # 也提取鍵名中的文字
                    if isinstance(key, str):
                        cleaned_key = self._clean_text(key)
                        if cleaned_key and len(cleaned_key) > 1:
                            texts.append(cleaned_key)
                    _extract_recursive(value, depth + 1)
            
            elif isinstance(data, list):
                for item in data:
                    _extract_recursive(item, depth + 1)
        
        _extract_recursive(json_data)
        return texts
    
    def _clean_text(self, text: str) -> str:
        """清理文字，移除多餘的空白和特殊字符"""
        if not text:
            return ""
        
        # 移除HTML標籤
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多餘的空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 移除純數字和純英文（根據需求調整）
        if re.match(r'^[0-9\s\-\.]+$', text) or re.match(r'^[a-zA-Z\s]+$', text):
            return ""
        
        return text
    
    def identify_difficult_words(self, texts: List[str], model) -> List[str]:
        """
        使用AI識別困難詞彙
        
        Args:
            texts: 文字列表
            model: Gemini模型
            
        Returns:
            困難詞彙列表
        """
        # 合併所有文字
        combined_text = " ".join(texts)
        
        # 如果文字太長，截取前面部分
        if len(combined_text) > 8000:
            combined_text = combined_text[:8000] + "..."
        
        prompt = f"""
        你是一位專業的中文語言分析師。請從以下文字中識別出可能對一般讀者來說比較困難、專業或不常見的詞彙。

        請遵循以下標準：
        1. 專業術語（如：法律、醫學、科技等領域的專有名詞）
        2. 不常用的詞彙或成語
        3. 外來語音譯詞
        4. 縮寫或簡稱
        5. 長度在2-8個字的詞彙

        請排除：
        - 常見的日常用語
        - 人名、地名（除非是專業術語）
        - 純數字或日期
        - 單個字符

        請以JSON格式回傳困難詞彙列表，格式如下：
        {{"difficult_words": ["詞彙1", "詞彙2", "詞彙3"]}}

        要分析的文字：
        {combined_text}
        """
        
        try:
            response = model.generate_content(prompt)
            cleaned_text = response.text.strip()
            
            # 清理回應
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:].strip()
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3].strip()
            
            result = json.loads(cleaned_text)
            difficult_words = result.get("difficult_words", [])
            
            # 過濾停用詞和重複詞彙
            filtered_words = []
            for word in difficult_words:
                if (word not in self.stopwords and 
                    len(word) >= 2 and 
                    len(word) <= 8 and
                    word not in filtered_words):
                    filtered_words.append(word)
            
            return filtered_words[:20]  # 限制最多20個詞彙
            
        except Exception as e:
            print(f"識別困難詞彙時發生錯誤：{e}")
            return []

class SmartTextProcessor:
    """智能文本處理器 - 整合文本分析和詞彙解釋功能"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.analyzer = TextAnalyzer()
        self.api_key = api_key
        self.model = None
        self._setup_model()
    
    def _setup_model(self):
        """設置Gemini模型"""
        if not self.api_key:
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("錯誤：請設定 GEMINI_API_KEY 環境變數或提供 api_key 參數")
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
            print("✅ Gemini API 初始化成功")
        except Exception as e:
            raise RuntimeError(f"初始化 Gemini 時發生錯誤: {e}")
    
    def process_json_file(self, 
                         json_file: str, 
                         output_file: Optional[str] = None,
                         verbose: bool = True) -> Dict:
        """
        處理JSON檔案的完整流程
        
        Args:
            json_file: 輸入的JSON檔案路徑
            output_file: 輸出檔案路徑（可選）
            verbose: 是否顯示詳細過程
            
        Returns:
            包含困難詞彙解釋的完整結果
        """
        if verbose:
            print(f"📖 開始處理檔案：{json_file}")
        
        # 步驟1：讀取JSON檔案
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            if verbose:
                print("✅ JSON檔案讀取成功")
        except Exception as e:
            raise FileNotFoundError(f"讀取JSON檔案失敗：{e}")
        
        # 步驟2：提取文字內容
        if verbose:
            print("🔍 正在提取文字內容...")
        texts = self.analyzer.extract_text_from_json(json_data)
        if verbose:
            print(f"✅ 已提取 {len(texts)} 段文字內容")
        
        if not texts:
            print("⚠️ 未找到任何文字內容")
            return {"texts": [], "difficult_words": [], "explanations": {"terms": []}}
        
        # 步驟3：識別困難詞彙
        if verbose:
            print("🧠 正在識別困難詞彙...")
        difficult_words = self.analyzer.identify_difficult_words(texts, self.model)
        if verbose:
            print(f"✅ 識別出 {len(difficult_words)} 個困難詞彙：{difficult_words}")
        
        if not difficult_words:
            print("ℹ️ 未識別出困難詞彙")
            return {"texts": texts, "difficult_words": [], "explanations": {"terms": []}}
        
        # 步驟4：生成詞彙解釋
        if verbose:
            print("📝 正在生成詞彙解釋...")
        explanations = self._explain_words(difficult_words, verbose)
        
        # 步驟5：組合最終結果
        final_result = {
            "source_file": json_file,
            "processing_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "extracted_texts_count": len(texts),
            "extracted_texts": texts[:5],  # 只保留前5段作為樣本
            "difficult_words_count": len(difficult_words),
            "difficult_words": difficult_words,
            "explanations": explanations
        }
        
        # 步驟6：儲存結果（如果指定了輸出檔案）
        if output_file:
            self._save_result(final_result, output_file, verbose)
        
        if verbose:
            print("🎉 處理完成！")
        
        return final_result
    
    def _explain_words(self, words: List[str], verbose: bool = True) -> Dict:
        """生成詞彙解釋"""
        terms_list = []
        
        prompt_template = """
        你是一位知識淵博的詞典編纂專家。
        針對以下提供的詞彙，請提供約50字的「名詞解釋」和「應用範例」。
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

        for i, word in enumerate(words, 1):
            if verbose:
                print(f"  📝 解釋詞彙 ({i}/{len(words)})：「{word}」...")
            
            prompt = prompt_template.format(word=word)
            
            try:
                response = self.model.generate_content(prompt)
                
                # 清理回應文字
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:].strip()
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3].strip()
                
                # 解析JSON回應
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
                
                # 延遲以避免超過API速率限制
                if i < len(words):
                    time.sleep(1)
                
            except json.JSONDecodeError:
                if verbose:
                    print(f"    ⚠️ 解析詞彙「{word}」的回應失敗，跳過")
                continue
            except Exception as e:
                if verbose:
                    print(f"    ⚠️ 解釋詞彙「{word}」時發生錯誤：{e}")
                continue
        
        return {"terms": terms_list}
    
    def _save_result(self, result: Dict, output_file: str, verbose: bool = True):
        """儲存結果到檔案"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if verbose:
                print(f"💾 結果已儲存到：{output_file}")
        except Exception as e:
            print(f"❌ 儲存檔案失敗：{e}")

def main():
    """主程式"""
    import sys
    
    print("🚀 智能文本分析與詞彙解釋程式")
    print("=" * 50)
    
    # 檢查命令列參數
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # 互動模式
        input_file = input("請輸入JSON檔案路徑：").strip()
        output_file = input("請輸入輸出檔案路徑（直接按Enter跳過）：").strip()
        if not output_file:
            output_file = None
    
    if not input_file:
        print("❌ 請提供JSON檔案路徑")
        return
    
    try:
        # 創建處理器並執行
        processor = SmartTextProcessor()
        result = processor.process_json_file(input_file, output_file)
        
        # 顯示結果摘要
        print("\n📊 處理結果摘要：")
        print("=" * 30)
        print(f"來源檔案：{result['source_file']}")
        print(f"處理時間：{result['processing_date']}")
        print(f"提取文字段數：{result['extracted_texts_count']}")
        print(f"識別困難詞彙數：{result['difficult_words_count']}")
        print(f"成功解釋詞彙數：{len(result['explanations']['terms'])}")
        
        if result['difficult_words']:
            print(f"\n🔤 困難詞彙：{', '.join(result['difficult_words'])}")
        
        if not output_file:
            print("\n📝 完整結果：")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ 執行失敗：{e}")

if __name__ == "__main__":
    main()
