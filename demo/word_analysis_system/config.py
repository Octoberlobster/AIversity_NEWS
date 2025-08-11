# config.py
import os

class Config:
    """配置類別，管理所有檔案路徑和系統設定"""
    
    # 基本資料夾設定
    BASE_FOLDER = 'keyword_analysis_output'
    
    # 輸入檔案設定
    INPUT_FILES = {
        'comprehensive_reports': 'final_comprehensive_reports_20250811_184840.json',
    }
    
    # 輸出檔案設定
    OUTPUT_FILES = {
        'keyword_explanations': 'keyword_explanations.json',
    }
    
    # API 相關設定
    API_CONFIG = {
        'model_name': 'gemini-1.5-pro',
        'call_delay_seconds': 1,  # API 呼叫間隔（秒）
        'max_retries': 3,         # 最大重試次數
    }
    
    # 處理設定
    PROCESSING_CONFIG = {
        'keywords_to_extract': 8,      # 每個版本要提取的關鍵字數量
        'versions_to_process': ['ultra_short', 'short', 'long'], # 要處理的版本類型
        'explanation_word_limit': 50,  # 詞彙解釋的建議字數
    }
    
    @classmethod
    def get_input_file_path(cls, file_key: str) -> str:
        """取得輸入檔案的完整路徑"""
        filename = cls.INPUT_FILES.get(file_key)
        if not filename:
            raise ValueError(f"找不到輸入檔案設定: {file_key}")
        return filename
    
    @classmethod
    def get_output_file_path(cls, file_key: str) -> str:
        """取得輸出檔案的完整路徑"""
        filename = cls.OUTPUT_FILES.get(file_key)
        if not filename:
            raise ValueError(f"找不到輸出檔案設定: {file_key}")
        cls.ensure_folders_exist()
        return os.path.join(cls.BASE_FOLDER, filename)
    
    @classmethod
    def ensure_folders_exist(cls):
        """確保輸出資料夾存在"""
        os.makedirs(cls.BASE_FOLDER, exist_ok=True)

