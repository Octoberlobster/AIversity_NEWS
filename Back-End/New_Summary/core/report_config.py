"""
報導生成器配置檔案
"""

import os
from typing import Dict, Any

# 嘗試載入 .env 檔案
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
except ImportError:
    pass

class ReportGeneratorConfig:
    """報導生成器配置類"""
    
    # API 設定
    @classmethod
    def get_gemini_api_key(cls):
        return os.getenv('GEMINI_API_KEY', '')
    
    GEMINI_MODEL = "gemini-2.0-flash"
    
    # 檔案路徑 - 相對於 core 模組的位置
    INPUT_DIR = os.path.join(os.path.dirname(__file__), "../outputs/processed/")
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../outputs/reports/")
    LOG_DIR = os.path.join(os.path.dirname(__file__), "../outputs/logs/")
    
    # 處理參數
    API_DELAY = 1.5  # API 調用間隔秒數（報導生成需要更多時間）
    BATCH_SAVE_SIZE = 2  # 每處理幾個 stories 後保存進度
    
    # 綜合報導設定
    COMPREHENSIVE_REPORT = {
        "min_articles": 2,            # 最少需要幾篇文章才生成綜合報導
        "max_keywords": 10,           # 綜合報導中最多包含的關鍵詞數量
        "max_persons": 5,             # 最多包含的重要人物數量
        "max_organizations": 5        # 最多包含的機構數量
    }

    # 綜合報導長度規範（三種版本）
    COMPREHENSIVE_LENGTHS = {
        "ultra_short": {  # 約 30 字
            "min_chars": 20,
            "max_chars": 40,
            "description": "極短版（約30字）"
        },
        "short": {        # 約 150 字
            "min_chars": 100,
            "max_chars": 180,
            "description": "短版（約150字）"
        },
        "long": {         # 約 300 字
            "min_chars": 250,
            "max_chars": 350,
            "description": "長版（約300字）"
        }
    }
    
    # Gemini 生成參數
    GENERATION_CONFIGS = {
        "short_summary": {
            "temperature": 0.2,
            "max_output_tokens": 150,
            "top_p": 0.7,
            "top_k": 20
        },
        "medium_summary": {
            "temperature": 0.3,
            "max_output_tokens": 400,
            "top_p": 0.8,
            "top_k": 25
        },
        "long_summary": {
            "temperature": 0.4,
            "max_output_tokens": 800,
            "top_p": 0.9,
            "top_k": 30
        },
        # 綜合報導三種版本的生成參數（可依需求調整）
        "comprehensive_ultra_short": {
            "temperature": 0.2,
            "max_output_tokens": 300,
            "top_p": 0.7,
            "top_k": 20
        },
        "comprehensive_short": {
            "temperature": 0.25,
            "max_output_tokens": 500,
            "top_p": 0.8,
            "top_k": 25
        },
        "comprehensive_long": {
            "temperature": 0.3,
            "max_output_tokens": 800,
            "top_p": 0.85,
            "top_k": 25
        }
    }
    
    # 安全設置
    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH", 
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
    
    # 品質控制設定
    QUALITY_CONTROL = {
        "min_confidence_score": 0.7,  # 只處理信心度大於此值的文章
        "require_keywords": True,      # 是否要求必須有關鍵詞
        "require_persons": False,      # 是否要求必須有人物資訊
        "max_retry_attempts": 3        # API 調用失敗時的重試次數
    }
    
    @classmethod
    def ensure_directories(cls):
        """確保必要的目錄存在"""
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """驗證配置是否正確"""
        if not cls.get_gemini_api_key():
            print("錯誤: GEMINI_API_KEY 未設定")
            return False
        
        if not os.path.exists(cls.INPUT_DIR):
            print(f"錯誤: 輸入目錄不存在 - {cls.INPUT_DIR}")
            return False
        
        return True
    
    @classmethod
    def get_output_filename(cls, prefix: str = "generated_reports") -> str:
        """生成帶時間戳的輸出檔名"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{cls.OUTPUT_DIR}{prefix}_{timestamp}.json"
    
    @classmethod
    def find_latest_processed_file(cls) -> str:
        """尋找最新的處理檔案"""
        import glob
        
        pattern = f"{cls.INPUT_DIR}processed_articles_*.json"
        files = glob.glob(pattern)
        
        if not files:
            raise FileNotFoundError(f"在 {cls.INPUT_DIR} 中找不到已處理的新聞檔案")
        
        # 按修改時間排序，取最新的
        latest_file = max(files, key=os.path.getmtime)
        return latest_file
    
    @classmethod
    def should_process_article(cls, article_data: Dict) -> bool:
        """判斷文章是否符合處理條件"""
        confidence = article_data.get('confidence_score', 0)
        keywords = article_data.get('keywords', [])
        persons = article_data.get('key_persons', [])
        
        # 檢查信心度
        if confidence < cls.QUALITY_CONTROL['min_confidence_score']:
            return False
        
        # 檢查關鍵詞要求
        if cls.QUALITY_CONTROL['require_keywords'] and not keywords:
            return False
        
        # 檢查人物要求
        if cls.QUALITY_CONTROL['require_persons'] and not persons:
            return False
        
        return True
    
    @classmethod
    def should_generate_comprehensive_report(cls, articles_count: int) -> bool:
        """判斷是否應該生成綜合報導"""
        return articles_count >= cls.COMPREHENSIVE_REPORT['min_articles']
