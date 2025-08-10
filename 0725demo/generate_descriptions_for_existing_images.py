#!/usr/bin/env python3
"""
為已存在的圖片批量生成說明的工具
"""

import os
import json
import glob
from typing import Dict, Any
from generate_picture.core import _load_json, _generate_image_description, _safe_slug

def generate_descriptions_for_existing_images(
    input_json: str,
    images_dir: str,
    output_json: str = "existing_images_metadata.json"
) -> Dict[str, Any]:
    """
    為現有的圖片生成說明文字並儲存到JSON檔案
    
    Args:
        input_json (str): 原始新聞JSON檔案路徑
        images_dir (str): 圖片資料夾路徑
        output_json (str): 輸出的metadata JSON檔案名稱
        
    Returns:
        Dict[str, Any]: 處理結果統計
    """
    
    # 載入新聞資料
    articles = _load_json(input_json)
    
    # 建立文章索引 (title -> article data)
    article_index = {}
    for art in articles:
        title = art.get("article_title") or art.get("title") or "untitled"
        article_index[_safe_slug(title, maxlen=70)] = art
    
    # 尋找所有圖片檔案
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend(glob.glob(os.path.join(images_dir, "**", ext), recursive=True))
    
    image_metadata = []
    matched_count = 0
    unmatched_count = 0
    
    print(f"找到 {len(image_files)} 個圖片檔案")
    
    for img_path in image_files:
        # 從檔案路徑推斷文章資訊
        rel_path = os.path.relpath(img_path, images_dir)
        category_dir = os.path.dirname(rel_path)
        filename = os.path.basename(img_path)
        
        # 移除副檔名和可能的數字後綴
        base_name = os.path.splitext(filename)[0]
        if base_name.endswith('_1'):
            base_name = base_name[:-2]
        
        # 嘗試在文章索引中找到對應的文章
        article_data = article_index.get(base_name)
        
        if article_data:
            # 找到對應文章，生成說明
            title = article_data.get("article_title") or article_data.get("title") or "untitled"
            summary = article_data.get("article_summary") or article_data.get("summary") or article_data.get("content") or ""
            category = article_data.get("category") or article_data.get("story_category") or category_dir
            
            description = _generate_image_description(title, summary, category)
            
            image_metadata.append({
                "image_path": img_path,
                "description": description,
                "article_title": title,
                "category": category,
                "article_id": article_data.get("id", ""),
                "matched": True
            })
            matched_count += 1
        else:
            # 未找到對應文章，使用基本資訊生成說明
            category = category_dir if category_dir else "misc"
            title = base_name.replace('-', ' ').title()
            
            description = f"新聞相關圖片：{title}"
            
            image_metadata.append({
                "image_path": img_path,
                "description": description,
                "article_title": title,
                "category": category,
                "article_id": "",
                "matched": False
            })
            unmatched_count += 1
    
    # 儲存metadata
    output_path = os.path.join(images_dir, output_json)
    metadata = {
        "total_images": len(image_metadata),
        "matched_articles": matched_count,
        "unmatched_images": unmatched_count,
        "generated_at": __import__('time').strftime("%Y-%m-%d %H:%M:%S"),
        "source_json": input_json,
        "images_directory": images_dir,
        "images": image_metadata
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    return {
        "total_images": len(image_metadata),
        "matched_articles": matched_count,
        "unmatched_images": unmatched_count,
        "output_path": output_path
    }

def main():
    """主函數 - 使用範例"""
    
    # 設定參數
    input_json = "cleaned_final_news1.json"
    images_dir = "generated_images"  # 修改為你的圖片資料夾路徑
    
    print("開始為現有圖片生成說明...")
    print(f"新聞資料來源: {input_json}")
    print(f"圖片資料夾: {images_dir}")
    
    if not os.path.exists(images_dir):
        print(f"❌ 圖片資料夾不存在: {images_dir}")
        return
    
    if not os.path.exists(input_json):
        print(f"❌ 新聞JSON檔案不存在: {input_json}")
        return
    
    # 執行處理
    result = generate_descriptions_for_existing_images(
        input_json=input_json,
        images_dir=images_dir
    )
    
    # 顯示結果
    print("\n=== 處理結果 ===")
    print(f"總圖片數: {result['total_images']}")
    print(f"成功配對文章: {result['matched_articles']}")
    print(f"未配對圖片: {result['unmatched_images']}")
    print(f"輸出檔案: {result['output_path']}")
    
    # 顯示部分範例
    if os.path.exists(result['output_path']):
        with open(result['output_path'], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print("\n=== 說明範例 ===")
        for i, img_info in enumerate(metadata['images'][:3]):
            print(f"\n圖片 {i+1}:")
            print(f"  檔案: {os.path.basename(img_info['image_path'])}")
            print(f"  說明: {img_info['description']}")
            print(f"  類別: {img_info['category']}")
            print(f"  配對成功: {img_info['matched']}")
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
