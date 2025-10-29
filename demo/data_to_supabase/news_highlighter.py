"""
新聞重點標記器
從 Supabase single_news 表讀取資料，標記重要字句並儲存為 JSON

用法:
  處理所有資料: python news_highlighter.py
  限制筆數: python news_highlighter.py [limit]
  測試單一新聞: python news_highlighter.py test [story_id]

範例:
  python news_highlighter.py                    # 處理所有資料
  python news_highlighter.py 10                # 處理前 10 筆資料
  python news_highlighter.py test abc123       # 測試 story_id = abc123 的新聞

請在 .env 檔案中設定 GEMINI_API_KEY、SUPABASE_URL 與 SUPABASE_KEY
"""

import os
import json
import time
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

# 載入環境變數
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請在 .env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("請在 .env 設定 GEMINI_API_KEY")
    sys.exit(1)

try:
    from supabase import create_client
    print("✓ Supabase 套件已載入")
except ImportError:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    sys.exit(1)

try:
    import google.genai as genai
    print("✓ Google Genai 套件已載入")
except ImportError:
    print("請先安裝 google genai SDK：pip install google-genai")
    sys.exit(1)


class NewsHighlighterConfig:
    """新聞重點標記器設定"""
    
    # API 設定
    API_CONFIG = {
        'model_name': 'gemini-2.5-flash',
        'call_delay_seconds': 1,  # API 呼叫間隔
        'max_retries': 3,
    }
    
    # 處理設定
    PROCESSING_CONFIG = {
        'max_highlights': 10,  # 每篇新聞最多標記幾處重點
        'min_highlights': 3,   # 每篇新聞至少標記幾處重點
        'default_limit': None,  # 預設讀取筆數限制
    }
    
    # 資料庫設定
    DB_CONFIG = {
        'table_name': 'single_news',
        'select_fields': ['story_id', 'news_title', 'long', 'long_en_lang', 'long_jp_lang', 'long_id_lang'],
        'primary_content_field': 'long',  # 主要用於標記的欄位
        'title_field': 'news_title',
        'multilang_fields': {
            'zh': 'long',
            'en': 'long_en_lang',
            'jp': 'long_jp_lang', 
            'id': 'long_id_lang'
        }
    }
    
    # 輸出設定
    OUTPUT_CONFIG = {
        'output_dir': 'news_highlights',  # 輸出目錄
        'output_filename_template': 'news_highlights_{timestamp}.json',  # 輸出檔名模板
    }


class NewsHighlighter:
    """新聞重點標記的核心類別"""

    def __init__(self):
        """初始化新聞重點標記器"""
        self.genai_client = None
        self.supabase_client = None
        self.api_config = NewsHighlighterConfig.API_CONFIG
        self.proc_config = NewsHighlighterConfig.PROCESSING_CONFIG
        self.db_config = NewsHighlighterConfig.DB_CONFIG
        self.output_config = NewsHighlighterConfig.OUTPUT_CONFIG
        self._setup_model()
        self._setup_supabase()

    def _setup_model(self):
        """初始化 Gemini 模型"""
        try:
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            print(f"✓ Gemini Client ({self.api_config['model_name']}) 初始化成功")
        except Exception as e:
            print(f"✗ Gemini Client 初始化失敗: {e}")
            raise

    def _setup_supabase(self):
        """初始化 Supabase 連線"""
        from supabase import create_client
        self.supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✓ Supabase 連線 ({SUPABASE_URL}) 初始化成功")

    def is_ready(self) -> bool:
        """檢查模型和資料庫連線是否已成功初始化"""
        return self.genai_client is not None and self.supabase_client is not None

    def _clean_response_text(self, text: str) -> str:
        """清理 Gemini 回覆中的 markdown JSON 標籤"""
        cleaned_text = text.strip()
        # 檢查並移除開頭的 markdown 標籤
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        # 檢查並移除結尾的 markdown 標籤
        if cleaned_text.endswith("```json"):
            cleaned_text = cleaned_text[:-7]
        elif cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
            
        return cleaned_text.strip()

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """呼叫 Gemini API 並處理回覆"""
        for attempt in range(self.api_config['max_retries']):
            try:
                response = self.genai_client.models.generate_content(
                    model=self.api_config['model_name'],
                    contents=prompt
                )
                cleaned_text = self._clean_response_text(response.text)
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                print(f"✗ JSON 解析錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    print(f"原始回覆: {response.text}")
                    return {}
            except Exception as e:
                print(f"✗ API 呼叫時發生錯誤 (嘗試 {attempt + 1}/{self.api_config['max_retries']}): {e}")
                if attempt == self.api_config['max_retries'] - 1:
                    return {}
                time.sleep(2)  # 重試前等待
        return {}

    def fetch_news_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """從 Supabase 讀取 single_news 資料"""
        print("\n=== 讀取新聞資料 ===")
        
        try:
            table_name = self.db_config['table_name']
            fields = ','.join(self.db_config['select_fields'])
            
            query = self.supabase_client.table(table_name).select(fields)
            
            if limit:
                query = query.limit(limit)
                print(f"限制讀取前 {limit} 筆")
            else:
                print("讀取所有資料")
            
            resp = query.execute()
            
            if getattr(resp, 'error', None):
                print(f"讀取 {table_name} 失敗: {resp.error}")
                return []
            
            news_data = resp.data or []
            print(f"✓ 成功讀取 {len(news_data)} 筆新聞資料")
            return news_data
            
        except Exception as e:
            print(f"✗ 讀取新聞資料時發生錯誤: {e}")
            return []

    def extract_highlights(self, content: str, title: str) -> List[str]:
        """從新聞內容中提取重點字句"""
        max_highlights = self.proc_config['max_highlights']
        min_highlights = self.proc_config['min_highlights']
        
        prompt = f"""
你是一位資深新聞編輯，必須從新聞中嚴格篩選出「真正的核心重點」。

**嚴格審查標準：**

必須符合以下至少2項條件才算是「真正重點」：
1. **硬數據/具體事實**：包含明確的數字、日期、地點、人名、機構名稱等可驗證的事實
2. **決策性資訊**：重大決定、政策變動、關鍵轉折、突破性進展
3. **因果關係**：解釋事件發生的原因或可能造成的影響/後果
4. **獨特價值**：新發現、首次、唯一、罕見等具有新聞稀缺性的內容
5. **行動指令**：明確的計畫、時間表、執行方案

**嚴格排除的內容：**
❌ 背景鋪陳、常識性描述
❌ 情緒化形容詞或主觀評論
❌ 重複標題的內容
❌ 籠統的總結性語句(例如：「此事件引發熱議」「影響深遠」等空泛描述)
❌ 純粹連接性的句子(例如：「與此同時」「此外」開頭的句子)

新聞標題：{title}
新聞內容：
{content}

請嚴格以 JSON 格式回傳，每個重點必須包含實質內容：
{{
  "highlights": [
    "包含具體事實、數據或關鍵決策的完整原文",
    "另一個符合標準的核心資訊原文"
  ]
}}

**要求：**
- 數量：{min_highlights}-{max_highlights} 個（寧缺勿濫，如果真正重點不足 {min_highlights} 個，也不要湊數）
- 引用：必須一字不改地引用原文
- 長度：每個重點 15-80 字為佳
- 品質：每個都必須是「讀者必須知道的核心資訊」，而非「錦上添花的補充說明」
"""
        
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        return result.get('highlights', [])

    def match_multilang_highlights(self, zh_highlights: List[str], news_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """將中文重點匹配到其他語言版本的對應句子"""
        multilang_fields = self.db_config['multilang_fields']
        
        # 準備多語言內容
        contents = {}
        for lang, field in multilang_fields.items():
            content = news_data.get(field, '')
            if content and content.strip():
                contents[lang] = content
        
        # 如果沒有中文重點或其他語言內容,直接返回
        if not zh_highlights or len(contents) <= 1:
            return {lang: [] for lang in multilang_fields.keys() if lang != 'zh'}
        
        # 構建提示詞,讓 AI 找出對應的句子
        prompt = f"""
你是一位專業的多語言翻譯對照專家。現在有一篇新聞的中文版本和其他語言版本,請從其他語言版本中找出與中文重點對應的句子。

**中文重點句子：**
{json.dumps(zh_highlights, ensure_ascii=False, indent=2)}

**其他語言版本的完整內容：**

"""
        available_langs = []
        for lang in ['en', 'jp', 'id']:
            if lang in contents:
                available_langs.append(lang)
                lang_name = {'en': '英文', 'jp': '日文', 'id': '印尼文'}[lang]
                prompt += f"\n【{lang_name}版本】\n{contents[lang]}\n"
        
        prompt += f"""
如果違反以下規定，你將會遭受嚴重的懲罰。
**任務要求：**
1. 對於每個中文重點,在對應語言版本中找出「意思最接近」的句子
2. 必須一字不改地引用原文句子，包含標點符號(不要翻譯或改寫)
3. 如果某個語言版本找不到對應句子,該項目留空陣列 []
4. 保持與中文重點相同的順序

請以 JSON 格式回傳：
{{
  "en": ["對應第1個中文重點的英文句子", "對應第2個中文重點的英文句子", ...],
  "jp": ["對應第1個中文重點的日文句子", "對應第2個中文重點的日文句子", ...],
  "id": ["對應第1個中文重點的印尼文句子", "對應第2個中文重點的印尼文句子", ...]
}}

注意：
- 每個語言的陣列長度必須與中文重點數量一致({len(zh_highlights)}個)
- 如果找不到對應句子,該位置填入空字串 ""
- 只回傳存在內容的語言版本
"""
        
        result = self._call_gemini(prompt)
        time.sleep(self.api_config['call_delay_seconds'])
        
        # 確保返回格式正確
        matched_highlights = {}
        for lang in available_langs:
            matched_highlights[lang] = result.get(lang, [])
        
        return matched_highlights

    def save_to_database(self, results: List[Dict[str, Any]]) -> bool:
        """將重點標記結果儲存到 Supabase highlight 資料表
        
        Args:
            results: 包含重點標記結果的清單
            
        Returns:
            bool: 是否成功儲存
        """
        if not results:
            print("⚠ 沒有資料需要儲存")
            return False
        
        print("\n=== 開始儲存到資料庫 ===")
        
        success_count = 0
        error_count = 0
        
        for item in tqdm(results, desc="儲存資料"):
                try:
                    story_id = item['story_id']
                    highlights_zh = item['highlights_zh']
                    multilang = item.get('highlights_multilang', {})
                
                    # 準備插入資料（每種語言都包一層 highlight 陣列）
                    insert_data = {
                        'story_id': story_id,
                        'highlight': { 'highlight': highlights_zh },
                        'highlight_en_lang': { 'highlight': multilang.get('en', []) },
                        'highlight_jp_lang': { 'highlight': multilang.get('jp', []) },
                        'highlight_id_lang': { 'highlight': multilang.get('id', []) }
                    }
                
                    # 插入資料（使用 upsert 避免重複）
                    response = self.supabase_client.table('highlight').upsert(
                        insert_data,
                        on_conflict='story_id'
                    ).execute()
                
                    if getattr(response, 'error', None):
                        print(f"\n✗ story_id {story_id} 儲存失敗: {response.error}")
                        error_count += 1
                    else:
                        success_count += 1
                    
                except Exception as e:
                    print(f"\n✗ story_id {story_id} 發生錯誤: {e}")
                    error_count += 1
        
        # 顯示結果
        print(f"\n✓ 資料庫儲存完成:")
        print(f"  - 成功: {success_count} 筆")
        print(f"  - 失敗: {error_count} 筆")
        
        return error_count == 0

    def test_single_news(self, story_id: str):
        """測試單一新聞的重點標記"""
        print(f"\n=== 測試單一新聞重點標記 (story_id: {story_id}) ===")
        
        # 1. 從資料庫讀取指定新聞
        try:
            table_name = self.db_config['table_name']
            fields = ','.join(self.db_config['select_fields'])
            
            resp = self.supabase_client.table(table_name).select(fields).eq('story_id', story_id).execute()
            
            if getattr(resp, 'error', None):
                print(f"✗ 讀取新聞失敗: {resp.error}")
                return
            
            news_data = resp.data
            if not news_data:
                print(f"✗ 找不到 story_id: {story_id}")
                return
            
            news = news_data[0]
            title = news.get(self.db_config['title_field'], '未知標題')
            content = news.get(self.db_config['primary_content_field'], '')
            
            if not content:
                print(f"✗ story_id {story_id} 的內容為空")
                return
            
            print(f"✓ 成功讀取新聞: {title[:50]}...")
            print(f"✓ 內容長度: {len(content)} 字")
            
        except Exception as e:
            print(f"✗ 讀取新聞資料時發生錯誤: {e}")
            return
        
        # 2. 提取重點標記
        print("\n--- 提取重點標記 ---")
        highlights = self.extract_highlights(content, title)
        
        if not highlights:
            print("✗ 未找到任何重點標記")
            return
        
        # 2.5 匹配多語言重點
        print("\n--- 匹配多語言重點 ---")
        multilang_highlights = self.match_multilang_highlights(highlights, news)
        
        # 3. 顯示結果
        print("\n" + "=" * 80)
        print("重點標記結果 (含多語言)")
        print("=" * 80)
        print(f"新聞標題: {title}")
        print(f"story_id: {story_id}")
        print(f"標記數量: {len(highlights)}")
        
        print("\n" + "-" * 80)
        print("【中文重點】")
        print("-" * 80)
        for i, highlight in enumerate(highlights, 1):
            print(f"\n{i}. {highlight}")
        
        # 顯示多語言對應
        lang_names = {'en': '英文', 'jp': '日文', 'id': '印尼文'}
        for lang, lang_name in lang_names.items():
            if lang in multilang_highlights and multilang_highlights[lang]:
                print("\n" + "-" * 80)
                print(f"【{lang_name}重點】")
                print("-" * 80)
                for i, highlight in enumerate(multilang_highlights[lang], 1):
                    if highlight:
                        print(f"\n{i}. {highlight}")
                    else:
                        print(f"\n{i}. (無對應句子)")
        
        # 4. 儲存結果到 JSON
        result = {
            'story_id': story_id,
            'title': title,
            'highlights_zh': highlights,
            'highlights_multilang': multilang_highlights,
            'timestamp': datetime.now().isoformat()
        }
        
        # 建立輸出目錄
        output_dir = self.output_config['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # 儲存檔案
        output_file = os.path.join(output_dir, f"test_{story_id}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 結果已儲存至: {output_file}")
        
        # 5. 儲存到資料庫
        print("\n--- 儲存到資料庫 ---")
        try:
            insert_data = {
                'story_id': story_id,
                'highlight': {'highlight': highlights},
                'highlight_en_lang': {'highlight': multilang_highlights.get('en', [])},
                'highlight_jp_lang': {'highlight': multilang_highlights.get('jp', [])},
                'highlight_id_lang': {'highlight': multilang_highlights.get('id', [])}
            }
            
            response = self.supabase_client.table('highlight').upsert(
                insert_data,
                on_conflict='story_id'
            ).execute()
            
            if getattr(response, 'error', None):
                print(f"✗ 儲存到資料庫失敗: {response.error}")
            else:
                print(f"✓ 已成功儲存到資料庫 (story_id: {story_id})")
                
        except Exception as e:
            print(f"✗ 儲存到資料庫時發生錯誤: {e}")

    def run(self, limit: Optional[int] = None):
        """執行完整的新聞重點標記流程"""
        if not self.is_ready():
            print("✗ 系統未就緒，無法執行")
            return

        print("\n" + "=" * 80)
        print("  新聞重點標記系統")
        print("=" * 80)

        # 1. 讀取新聞資料
        news_data = self.fetch_news_data(limit)
        if not news_data:
            print("未取得任何資料")
            return

        # 2. 處理每篇新聞
        print("\n=== 開始標記新聞重點 ===")
        results = []
        
        content_field = self.db_config['primary_content_field']
        title_field = self.db_config['title_field']
        
        for news in tqdm(news_data, desc="處理新聞"):
            story_id = news.get('story_id')
            if story_id is None:
                continue

            title = news.get(title_field, '未知標題')
            content = news.get(content_field, '')
            
            if not content:
                print(f"⚠ story_id {story_id} 的 {content_field} 欄位為空，跳過")
                continue
            
            # 提取中文重點標記
            highlights = self.extract_highlights(content, title)
            
            if highlights:
                # 匹配多語言重點
                multilang_highlights = self.match_multilang_highlights(highlights, news)
                
                results.append({
                    'story_id': story_id,
                    'title': title,
                    'highlights_zh': highlights,
                    'highlights_multilang': multilang_highlights,
                    'highlight_count': len(highlights)
                })

        print(f"✓ 處理完成：共標記 {len(results)} 篇新聞")

        # 3. 儲存結果到 JSON
        if results:
            # 建立輸出目錄
            output_dir = self.output_config['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成輸出檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = self.output_config['output_filename_template'].format(timestamp=timestamp)
            output_path = os.path.join(output_dir, output_filename)
            
            # 儲存結果
            output_data = {
                'total_news': len(results),
                'timestamp': datetime.now().isoformat(),
                'news_highlights': results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 結果已儲存至: {output_path}")
            
            # 4. 儲存到資料庫
            db_success = self.save_to_database(results)
            
            # 顯示統計資訊
            total_highlights = sum(item['highlight_count'] for item in results)
            avg_highlights = total_highlights / len(results) if results else 0
            
            print("\n" + "=" * 80)
            print("  執行完成摘要")
            print("=" * 80)
            print(f"✓ 處理新聞數量: {len(results)}")
            print(f"✓ 總標記數量: {total_highlights}")
            print(f"✓ 平均每篇標記: {avg_highlights:.1f} 處")
            print(f"✓ 輸出檔案: {output_path}")
            print(f"✓ 資料庫儲存: {'成功' if db_success else '部分失敗'}")
            print("=" * 80)


def main():
    """主程式入口"""
    print("=" * 80)
    print("  新聞重點標記系統")
    print("=" * 80)
    
    # 解析指令列參數
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # 檢查是否為測試模式
        if first_arg == "test" and len(sys.argv) > 2:
            story_id = sys.argv[2]
            print(f"✓ 測試模式: 使用 story_id = {story_id}")
            
            try:
                highlighter = NewsHighlighter()
                if highlighter.is_ready():
                    highlighter.test_single_news(story_id)
                else:
                    print("✗ 系統未就緒，無法執行測試")
            except EnvironmentError as e:
                print(f"✗ 環境錯誤：{e}")
                print("請檢查您的 .env 設定檔。")
            except Exception as e:
                print(f"✗ 發生未預期的錯誤：{e}")
            
            return
        
        # 一般模式：解析 limit 參數
        try:
            limit = int(first_arg)
            print(f"✓ 設定讀取限制: {limit} 筆")
        except ValueError:
            print("⚠ 無效的 limit 參數，將讀取所有資料")
            limit = None
    else:
        limit = None
        print("✓ 一般模式: 處理所有資料")
    
    try:
        # 初始化並執行處理器
        highlighter = NewsHighlighter()
        if highlighter.is_ready():
            highlighter.run(limit)
        
    except EnvironmentError as e:
        print(f"✗ 環境錯誤：{e}")
        print("請檢查您的 .env 設定檔。")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 發生未預期的錯誤：{e}")
        sys.exit(1)
        
    print("\n" + "=" * 80)
    print("系統執行完畢。")
    print("=" * 80)


if __name__ == "__main__":
    main()
