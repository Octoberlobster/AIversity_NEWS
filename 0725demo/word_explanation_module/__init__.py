"""
詞彙解釋模組 - Word Explanation Module

用於自動產生困難詞彙的解釋和應用範例的 Python 模組。

主要類別:
    WordExplainer: 詞彙解釋器類別

便利函數:
    explain_words: 快速解釋詞彙
    explain_from_file: 從檔案解釋詞彙

使用範例:
    >>> from word_explainer import WordExplainer, explain_words
    >>> result = explain_words("人工智慧")
    >>> print(result)
"""

from .word_explainer import WordExplainer, explain_words, explain_from_file

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "WordExplainer",
    "explain_words", 
    "explain_from_file"
]
