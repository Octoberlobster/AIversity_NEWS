"""
新聞關鍵字分析系統
處理綜合報導並提取關鍵字
"""

from .keyword_processor import (
    NewsKeywordProcessor,
    process_keywords_from_comprehensive_reports
)
from .config import Config

__version__ = "1.0.0"

__all__ = [
    "NewsKeywordProcessor",
    "process_keywords_from_comprehensive_reports",
    "Config"
]

# 系統資訊
SYSTEM_INFO = {
    "name": "新聞關鍵字分析系統",
    "version": __version__,
    "description": "從綜合新聞報導中提取關鍵字，支援多版本內容分析",
    "supported_versions": ["ultra_short", "short", "long"]
}

def get_system_info():
    """取得系統資訊"""
    return SYSTEM_INFO.copy()
