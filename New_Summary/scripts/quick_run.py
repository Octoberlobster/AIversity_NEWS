"""
快速執行腳本 - 一鍵完成新聞處理和報導生成
"""

import os
import sys
import json
from datetime import datetime

# 確保載入 .env 檔案
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 添加父目錄到 Python 路徑，以便引用 core 模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run_complete_pipeline import CompletePipeline

def quick_run():
    """快速執行完整流水線"""
    
    print("新聞處理 + 報導生成 一鍵執行")
    print("="*40)
    
    # 檢查環境
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("請先設定 GEMINI_API_KEY 環境變數")
        return
    
    print("環境檢查通過")
    print("開始處理...")
    
    try:
        # 創建並執行流水線
        pipeline = CompletePipeline(api_key=api_key)
        pipeline.run_complete_pipeline()

    except Exception as e:
        print(f"\n 執行失敗：{e}")

if __name__ == "__main__":
    quick_run()
