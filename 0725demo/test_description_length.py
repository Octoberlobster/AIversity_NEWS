#!/usr/bin/env python3
"""
測試圖片說明長度的腳本
"""

from generate_picture.core import _generate_image_description

def test_description_length():
    """測試說明文字長度是否符合15字限制"""
    
    # 測試案例
    test_cases = [
        {
            "title": "北檢譴責柯文哲暴走黃國昌諷：自知理虧的小孩哭著回家找媽媽| 政治",
            "summary": "民眾黨前主席柯文哲涉京華城案至今仍遭羈押...",
            "category": "政治"
        },
        {
            "title": "柯P休庭怒斥檢察官 北檢譴責",
            "summary": "柯文哲在法庭上情緒激動...",
            "category": "政治"
        },
        {
            "title": "京華城案再開庭 柯文哲休庭時怒罵檢察官 ｜ 公視新聞網 PNN",
            "summary": "京華城案再次開庭審理...",
            "category": "政治"
        },
        {
            "title": "科技業人工智慧發展迅速帶動經濟成長",
            "summary": "AI技術不斷進步...",
            "category": "科技"
        },
        {
            "title": "短標題",
            "summary": "簡短摘要",
            "category": "社會"
        },
        {
            "title": "這是一個非常非常長的新聞標題用來測試字數限制功能是否正常運作",
            "summary": "測試摘要",
            "category": "財經"
        }
    ]
    
    print("🧪 測試完整說明文字（最多15字，確保句子完整）")
    print("=" * 60)
    
    all_pass = True
    
    for i, case in enumerate(test_cases, 1):
        description = _generate_image_description(
            case["title"], 
            case["summary"], 
            case["category"]
        )
        
        char_count = len(description)
        
        # 改進的完整性檢查
        incomplete_endings = ['檢', '察', '的', '了', '在', '與', '對']
        # 完整詞彙的例外
        complete_exceptions = ['檢察官', '黃國昌', '柯文哲', '北檢', '檢察']
        
        is_complete = True
        for ending in incomplete_endings:
            if description.endswith(ending):
                # 檢查是否為完整詞彙的一部分
                is_exception = any(description.endswith(exc) for exc in complete_exceptions)
                if not is_exception:
                    is_complete = False
                    break
        
        # 額外檢查：確保不是明顯的截斷
        if len(description) == 15 and not description.endswith(('。', '！', '？', '事件', '行為', '活動')):
            # 如果剛好15字且沒有明顯的結尾，可能是截斷
            is_complete = is_complete and description[-2:] not in ['檢察', '國昌', '文哲']
        
        status = "✅ 通過" if char_count <= 15 and is_complete else "❌ 問題"
        
        if char_count > 15 or not is_complete:
            all_pass = False
        
        print(f"\n測試案例 {i}:")
        print(f"  類別: {case['category']}")
        print(f"  原標題: {case['title'][:40]}...")
        print(f"  生成說明: {description}")
        print(f"  字數: {char_count}/15")
        print(f"  句子完整: {'是' if is_complete else '否'}")
        print(f"  狀態: {status}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 所有測試通過！說明文字都在15字以內且句子完整")
    else:
        print("⚠️  部分測試未通過，需要調整")
    
    # 顯示各類新聞的說明範例
    print("\n📝 各類新聞的完整說明範例:")
    sample_titles = [
        ("柯文哲譴責檢察官不當行為", "政治"),
        ("AI技術突破發展迅速", "科技"), 
        ("社會福利政策討論熱烈", "社會"),
        ("股市大漲創歷史新高", "財經"),
        ("台美外交會談順利", "國際"),
        ("環保法規修正通過", "環境"),
        ("奧運選手奪金凱旋", "體育")
    ]
    
    for title, category in sample_titles:
        desc = _generate_image_description(title, "測試摘要", category)
        incomplete_endings = ['檢', '察', '國', '昌', '文', '哲', '的', '了', '在', '與', '對']
        is_complete = not any(desc.endswith(ending) for ending in incomplete_endings)
        complete_mark = "✓" if is_complete else "✗"
        print(f"  {category}: {desc} ({len(desc)}字) {complete_mark}")

if __name__ == "__main__":
    test_description_length()
