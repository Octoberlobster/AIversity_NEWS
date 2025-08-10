#!/usr/bin/env python3
"""
測試圖片說明功能的腳本
"""

from generate_picture.core import _generate_image_description

def test_description_function():
    """測試說明文字生成功能"""
    
    # 測試案例
    test_cases = [
        {
            "title": "柯文哲譴責黃國昌暴走：自知理虧的小孩哭著回家找媽媽",
            "summary": "民眾黨前主席柯文哲涉京華城案至今仍遭羈押...",
            "category": "政治"
        },
        {
            "title": "京華城案再開庭 柯文哲休庭時怒罵檢察官",
            "summary": "京華城案再次開庭審理...",
            "category": "政治"
        },
        {
            "title": "科技業人工智慧發展迅速帶動經濟成長",
            "summary": "AI技術不斷進步...",
            "category": "科技"
        }
    ]
    
    print("🧪 測試圖片說明生成功能")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        description = _generate_image_description(
            case["title"], 
            case["summary"], 
            case["category"]
        )
        
        char_count = len(description)
        status = "✅" if char_count <= 15 else "❌"
        
        print(f"\n測試案例 {i}:")
        print(f"  標題: {case['title'][:30]}...")
        print(f"  類別: {case['category']}")
        print(f"  生成說明: {description}")
        print(f"  字數: {char_count}/15 {status}")

if __name__ == "__main__":
    test_description_function()
