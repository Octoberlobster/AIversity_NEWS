# main.py
from keyword_processor import KeywordProcessor
from config import Config
import sys

def main():
    """主程式入口"""
    print("=" * 60)
    print("  新聞關鍵字分析與解釋系統")
    print("=" * 60)
    
    try:
        # 讀取設定
        input_file = Config.get_input_file_path('comprehensive_reports')
        output_file = Config.get_output_file_path('keyword_explanations')
        
        print(f"讀取輸入檔案：{input_file}")
        print(f"預計輸出檔案：{output_file}")
        
        # 初始化並執行處理器
        processor = KeywordProcessor()
        if processor.is_ready():
            processor.run(input_file, output_file)
        
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
