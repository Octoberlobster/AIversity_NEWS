"""
詞彙解釋模組 - Word Explanation Module

用於自動產生困難詞彙的解釋和應用範例的 Python 模組。
"""

import json
import os
import time
from typing import List, Dict, Optional, Union
import google.generativeai as genai
from dotenv import load_dotenv


class WordExplainer:
    """詞彙解釋器類別
    
    用於自動產生困難詞彙的解釋和應用範例。
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = 'gemini-1.5-pro-latest'):
        """
        初始化詞彙解釋器
        
        Args:
            api_key: Gemini API 金鑰，如果不提供會從環境變數讀取
            model_name: 使用的 Gemini 模型名稱
        """
        self.model = None
        self.api_key = api_key
        self.model_name = model_name
        self._setup_environment_and_model()
    
    def _setup_environment_and_model(self):
        """載入環境變數並初始化 Gemini 模型"""
        if not self.api_key:
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("錯誤：讀取失敗，請確認 .env 檔案中已設定 GEMINI_API_KEY 或直接提供 api_key 參數")

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print("Gemini API 金鑰與模型初始化成功。")
        except Exception as e:
            raise RuntimeError(f"初始化 Gemini 時發生錯誤: {e}")
    
    def explain_words(self, words: Union[List[str], str], delay: float = 1.0, verbose: bool = True) -> Dict:
        """
        為詞彙列表產生解釋和範例
        
        Args:
            words: 要解釋的詞彙，可以是字串或字串列表
            delay: API 呼叫間的延遲時間（秒）
            verbose: 是否顯示處理進度
            
        Returns:
            包含詞彙解釋的字典，格式為 {"terms": [...]}
        """
        if isinstance(words, str):
            words = [words]
        
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

        for i, word in enumerate(words, 1):
            if verbose:
                print(f"正在查詢詞彙 ({i}/{len(words)})：「{word}」...")
            
            prompt = prompt_template.format(word=word)
            
            try:
                response = self.model.generate_content(prompt)
                
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
                
                # 延遲以避免超過 API 速率限制
                if i < len(words):  # 最後一個詞彙不需要延遲
                    time.sleep(delay)
                
            except json.JSONDecodeError:
                if verbose:
                    print(f"錯誤：即使清理過，仍然無法解析詞彙「{word}」的 API 回覆。跳過此詞彙。")
                    print("API 回覆內容：", response.text[:200] + "..." if len(response.text) > 200 else response.text)
                continue
            except Exception as e:
                if verbose:
                    print(f"查詢詞彙「{word}」時發生錯誤：{e}。跳過此詞彙。")
                continue
                
        return {"terms": terms_list}
    
    def explain_from_file(self, input_file: str, output_file: Optional[str] = None, verbose: bool = True) -> Dict:
        """
        從 JSON 檔案讀取詞彙並產生解釋
        
        Args:
            input_file: 輸入檔案路徑，應包含 {"difficult_words": [...]} 格式
            output_file: 輸出檔案路徑，如果不提供則不儲存檔案
            verbose: 是否顯示處理進度
            
        Returns:
            包含詞彙解釋的字典
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"錯誤：找不到檔案 '{input_file}'。")
        except json.JSONDecodeError:
            raise ValueError(f"錯誤：檔案 '{input_file}' 的 JSON 格式無效。")
        
        if 'difficult_words' not in data or not data['difficult_words']:
            raise ValueError(f"檔案 '{input_file}' 不包含 'difficult_words' 列表或列表為空。")
        
        words_to_explain = data['difficult_words']
        
        if verbose:
            print(f"從 '{input_file}' 讀取到 {len(words_to_explain)} 個詞彙")
            print("--- 開始進行詞彙解釋 ---")
        
        result = self.explain_words(words_to_explain, verbose=verbose)
        
        if verbose:
            print("--- 詞彙解釋結束 ---")
        
        if output_file and result.get('terms'):
            self.save_to_file(result, output_file, verbose=verbose)
        
        return result
    
    @staticmethod
    def save_to_file(data: Dict, filename: str, verbose: bool = True):
        """
        將資料儲存為 JSON 檔案
        
        Args:
            data: 要儲存的資料
            filename: 檔案名稱
            verbose: 是否顯示儲存訊息
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if verbose:
            term_count = len(data.get('terms', []))
            print(f"任務完成！成功將 {term_count} 個詞彙解釋儲存至 '{filename}'")
    
    @staticmethod
    def create_sample_input(words: List[str], filename: str = "difficult_words.json"):
        """
        創建範例輸入檔案
        
        Args:
            words: 詞彙列表
            filename: 檔案名稱
        """
        data = {"difficult_words": words}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已創建範例輸入檔案 '{filename}'")


# 便利函數
def explain_words(words: Union[List[str], str], api_key: Optional[str] = None, **kwargs) -> Dict:
    """
    快速解釋詞彙的便利函數
    
    Args:
        words: 要解釋的詞彙
        api_key: Gemini API 金鑰
        **kwargs: 其他參數傳遞給 WordExplainer.explain_words()
        
    Returns:
        包含詞彙解釋的字典
    """
    explainer = WordExplainer(api_key=api_key)
    return explainer.explain_words(words, **kwargs)


def explain_from_file(input_file: str, output_file: Optional[str] = None, api_key: Optional[str] = None, **kwargs) -> Dict:
    """
    從檔案解釋詞彙的便利函數
    
    Args:
        input_file: 輸入檔案路徑
        output_file: 輸出檔案路徑
        api_key: Gemini API 金鑰
        **kwargs: 其他參數傳遞給 WordExplainer.explain_from_file()
        
    Returns:
        包含詞彙解釋的字典
    """
    explainer = WordExplainer(api_key=api_key)
    return explainer.explain_from_file(input_file, output_file, **kwargs)


if __name__ == "__main__":
    # 範例使用方式
    print("詞彙解釋模組範例")
    print("="*50)
    
    # 創建範例輸入檔案
    sample_words = ["三級三審", "IRB"]
    WordExplainer.create_sample_input(sample_words)
    
    try:
        # 使用類別方式
        explainer = WordExplainer()
        result = explainer.explain_from_file("difficult_words.json", "word_explanations.json")
        print(f"成功解釋了 {len(result.get('terms', []))} 個詞彙")
        
    except Exception as e:
        print(f"執行時發生錯誤: {e}")
        print("這可能是因為 API 配額不足或網路問題")
