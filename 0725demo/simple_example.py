#!/usr/bin/env python3
"""
簡潔的圖片生成範例 - 直接函數調用
"""

from generate_picture import generate_from_json

def simple_generate():
    """最簡單的使用方式"""
    
    result = generate_from_json(
        input_json="cleaned_final_news1.json",
        output_dir="simple_output",
        max_items=3  # 只生成3張圖片作為測試
    )
    
    print(f"成功: {result['succeeded']}/{result['processed']}")
    print(f"圖片: {result['total_images']} 張")
    print(f"輸出: {result['output_dir']}")

if __name__ == "__main__":
    simple_generate()
