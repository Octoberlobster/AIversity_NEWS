#!/usr/bin/env python3
"""
驗證15字說明功能的快速範例
"""

from generate_picture import generate_from_json

def quick_test():
    """快速測試新的15字說明功能"""
    
    print("🧪 測試15字說明功能...")
    
    result = generate_from_json(
        input_json="cleaned_final_news1.json",
        output_dir="test_15_chars",
        max_items=2  # 只生成2張圖片測試
    )
    
    print(f"✅ 完成: {result['succeeded']}/{result['processed']}")
    
    # 檢查生成的說明
    if 'metadata_path' in result:
        import json
        import os
        
        if os.path.exists(result['metadata_path']):
            with open(result['metadata_path'], 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print("\n📝 生成的說明 (字數檢查):")
            for i, img_info in enumerate(metadata['images'], 1):
                desc = img_info['description']
                char_count = len(desc)
                status = "✅" if char_count <= 15 else "❌"
                print(f"  {i}. {desc} ({char_count}字) {status}")

if __name__ == "__main__":
    quick_test()
