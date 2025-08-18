"""仿照 word_analysis_system config.py，single_news 讀取器的設定檔

提供 single_news 處理的基本設定項目
"""
import os

class SingleNewsConfig:
    """Single News 處理器設定"""
    
    # 資料庫設定
    DB_CONFIG = {
        'table_name': 'single_news',
        'select_fields': ['story_id', 'ultra_short', 'short', 'long'],
        'default_limit': None,  # None = 讀取全部
    }
    
    # 顯示設定
    DISPLAY_CONFIG = {
        'short_preview_length': 100,    # short 欄位預覽長度
        'long_preview_length': 200,     # long 欄位預覽長度
        'show_empty_as': '<空>',        # 空值顯示方式
        'terminal_width': 80,           # 終端機寬度
    }
    
    # 環境變數設定
    ENV_CONFIG = {
        'supabase_url_key': 'SUPABASE_URL',
        'supabase_key_key': 'SUPABASE_KEY',
        'env_file_name': '.env',
    }
    
    @classmethod
    def get_db_table(cls) -> str:
        """取得資料庫表名稱"""
        return cls.DB_CONFIG['table_name']
    
    @classmethod
    def get_select_fields(cls) -> list:
        """取得要查詢的欄位列表"""
        return cls.DB_CONFIG['select_fields']
    
    @classmethod
    def get_preview_lengths(cls) -> dict:
        """取得預覽長度設定"""
        return {
            'short': cls.DISPLAY_CONFIG['short_preview_length'],
            'long': cls.DISPLAY_CONFIG['long_preview_length']
        }
    
    @classmethod
    def get_terminal_width(cls) -> int:
        """取得終端機寬度"""
        return cls.DISPLAY_CONFIG['terminal_width']
    
    @classmethod
    def get_empty_placeholder(cls) -> str:
        """取得空值顯示文字"""
        return cls.DISPLAY_CONFIG['show_empty_as']
