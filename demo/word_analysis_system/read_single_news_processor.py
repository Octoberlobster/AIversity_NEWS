"""仿照 word_processor，讀取 Supabase single_news 的 story_id、ultra_short、short、long 並印出

用法:
  python read_single_news_processor.py [limit]

請在 word_analysis_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY
"""
import os
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from single_news_config import SingleNewsConfig

# 確保能 import word_analysis_system 的模組
_this_dir = os.path.dirname(__file__)
_parent_dir = os.path.dirname(_this_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

class SingleNewsProcessor:
    """仿照 KeywordProcessor，處理 Supabase single_news 讀取的核心類別"""

    def __init__(self):
        """初始化單則新聞處理器"""
        self.supabase_client = None
        self._setup_supabase()

    def _setup_supabase(self):
        """載入環境變數並初始化 Supabase 連線"""
        load_dotenv()
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise EnvironmentError("錯誤：找不到 SUPABASE_URL 或 SUPABASE_KEY，請在 .env 檔案中設定")
        
        try:
            from supabase import create_client
            self.supabase_client = create_client(supabase_url, supabase_key)
            print(f"✓ Supabase 連線 ({supabase_url}) 初始化成功")
        except Exception as e:
            print(f"✗ 初始化 Supabase 時發生錯誤: {e}")
            print("請確認已安裝 supabase-py：pip install supabase-py postgrest-py")
            raise

    def is_ready(self) -> bool:
        """檢查 Supabase 連線是否已成功初始化"""
        return self.supabase_client is not None

    def fetch_single_news(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """從 Supabase single_news 表讀取資料"""
        print("讀取 single_news 資料...")
        
        try:
            # 使用設定檔中的表名稱和欄位
            table_name = SingleNewsConfig.get_db_table()
            fields = ','.join(SingleNewsConfig.get_select_fields())
            
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
            
            rows = resp.data or []
            print(f"成功讀取 {len(rows)} 筆資料")
            return rows
            
        except Exception as e:
            print(f"讀取資料時發生錯誤: {e}")
            return []

    def print_news_data(self, news_data: List[Dict[str, Any]]):
        """將新聞資料印出到終端機"""
        width = SingleNewsConfig.get_terminal_width()
        preview_lengths = SingleNewsConfig.get_preview_lengths()
        empty_placeholder = SingleNewsConfig.get_empty_placeholder()
        
        print("\n" + "=" * width)
        print("  SINGLE NEWS 資料列表")
        print("=" * width)
        
        for idx, news in enumerate(news_data, start=1):
            if not isinstance(news, dict):
                print(f"第 {idx} 筆: 非典型資料格式，跳過")
                continue
            
            story_id = news.get('story_id', 'N/A')
            ultra_short = news.get('ultra_short', '')
            short = news.get('short', '')
            long = news.get('long', '')
            
            print(f"\n第 {idx} 筆新聞:")
            print("-" * 40)
            print(f"Story ID    : {story_id}")
            print(f"Ultra Short : {ultra_short if ultra_short else empty_placeholder}")
            
            # 使用設定檔中的預覽長度
            short_display = short[:preview_lengths['short']] + '...' if short and len(short) > preview_lengths['short'] else short if short else empty_placeholder
            long_display = long[:preview_lengths['long']] + '...' if long and len(long) > preview_lengths['long'] else long if long else empty_placeholder
            
            print(f"Short       : {short_display}")
            print(f"Long        : {long_display}")
        
        print("\n" + "=" * width)
        print(f"總計顯示 {len(news_data)} 筆新聞資料")
        print("=" * width)

    def run(self, limit: Optional[int] = None):
        """執行完整的讀取與顯示流程"""
        if not self.is_ready():
            print("✗ Supabase 連線未就緒，無法執行")
            return
        
        print("-" * 60)
        
        # 讀取資料
        news_data = self.fetch_single_news(limit)
        
        if not news_data:
            print("未取得任何資料")
            return
        
        # 印出資料
        self.print_news_data(news_data)

def main():
    """主程式入口"""
    print("=" * 60)
    print("  SINGLE NEWS 資料讀取器")
    print("=" * 60)
    
    # 解析命令列參數
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"限制讀取: {limit} 筆")
        except ValueError:
            print("無效的 limit 參數，使用預設值（讀取所有）")
    
    try:
        # 初始化並執行處理器
        processor = SingleNewsProcessor()
        if processor.is_ready():
            processor.run(limit)
        
    except EnvironmentError as e:
        print(f"✗ 系統錯誤：{e}")
        print("請檢查您的 .env 設定檔。")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 發生未預期的錯誤：{e}")
        sys.exit(1)
        
    print("=" * 60)
    print("系統執行完畢。")
    print("=" * 60)

if __name__ == "__main__":
    main()
