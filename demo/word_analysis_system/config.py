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
        'model_name': 'gemini-2.5-flash',  # 正確的模型名稱
        'call_delay_seconds': 1,  # API 呼叫間隔（秒）
        'max_retries': 3,         # 最大重試次數
    }
    
    # 處理設定
    PROCESSING_CONFIG = {
        'keywords_to_extract': 8,      # 每個文本要提取的關鍵字數量
        'explanation_word_limit': 50,  # 詞彙解釋的建議字數
    }
    
    @classmethod
    def get_input_file_path(cls, file_key: str) -> str:
        """取得輸入檔案的完整路徑"""
        filename = cls.INPUT_FILES.get(file_key)
        if not filename:
            raise ValueError(f"找不到輸入檔案設定: {file_key}")
        # 檢查檔案是否存在於當前目錄
        if os.path.exists(filename):
            return filename
        # 檢查檔案是否存在於上一層目錄
        parent_path = os.path.join('..', filename)
        if os.path.exists(parent_path):
            return parent_path
        raise FileNotFoundError(f"找不到輸入檔案: {filename}")
    
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

    # --- Supabase 設定 (可選) ---
    USE_SUPABASE = False
    # Supabase tables mapping (可修改為您資料庫中的實際表格名稱)
    SUPABASE_TABLES = {
        'comprehensive_reports': 'comprehensive_reports',
        'keyword_explanations': 'keyword_explanations'
    }

    @classmethod
    def get_supabase_table(cls, key: str) -> str:
        name = cls.SUPABASE_TABLES.get(key)
        if not name:
            raise ValueError(f"找不到 Supabase table 設定: {key}")
        return name

