"""仿照 word_analysis_system main.py，執行 single_news 資料讀取

用法:
  python main_single_news.py [limit]
  
limit: 可選，限制讀取筆數
"""
import os
import sys
from read_single_news_processor import SingleNewsProcessor

def main():
    """主執行入口"""
    print("=" * 80)
    print("  仿照 word_processor 的 SINGLE NEWS 資料讀取系統")
    print("=" * 80)
    
    # 解析指令列參數 (如果有的話)
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"✓ 設定讀取限制: {limit} 筆")
        except ValueError:
            print("⚠ 無效的 limit 參數，將讀取所有資料")
            limit = None
    
    # 初始化處理器
    try:
        print("\n正在初始化 Single News 處理器...")
        processor = SingleNewsProcessor()
        
        # 檢查處理器是否就緒
        if not processor.is_ready():
            print("✗ 處理器初始化失敗")
            return
        
        print("✓ 處理器就緒")
        
        # 執行處理
        print("\n開始處理...")
        processor.run(limit)
        
    except Exception as e:
        print(f"✗ 執行過程中發生錯誤: {e}")
        return

if __name__ == "__main__":
    main()
