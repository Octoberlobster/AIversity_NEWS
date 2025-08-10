#!/usr/bin/env python3
"""
測試圖片生成與說明功能的範例腳本
"""

import os
import json
from generate_picture import generate_from_json

def main():
    # 設定參數
    input_json = "cleaned_final_news1.json"
    output_dir = "generated_images_with_descriptions"
    
    # 限制生成數量以便測試（設為 None 可生成全部）
    max_items = 5
    
    print("開始生成圖片並建立說明...")
    print(f"輸入檔案: {input_json}")
    print(f"輸出目錄: {output_dir}")
    print(f"最大處理數量: {max_items if max_items else '全部'}")
    
    # 執行圖片生成
    result = generate_from_json(
        input_json=input_json,
        output_dir=output_dir,
        max_items=max_items,
        max_images_per_article=1,
        retry_times=3,
        sleep_between_calls=0.6
    )
    
    # 顯示結果
    print("\n=== 執行結果 ===")
    print(f"處理文章數: {result['processed']}")
    print(f"成功生成: {result['succeeded']}")
    print(f"失敗數量: {result['failed']}")
    print(f"錯誤數量: {result['errors_count']}")
    print(f"總圖片數: {result['total_images']}")
    print(f"輸出目錄: {result['output_dir']}")
    print(f"Metadata檔案: {result['metadata_path']}")
    
    # 讀取並顯示部分metadata內容
    if os.path.exists(result['metadata_path']):
        with open(result['metadata_path'], 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print("\n=== 圖片說明範例 ===")
        for i, img_info in enumerate(metadata['images'][:3]):  # 只顯示前3個
            print(f"\n圖片 {i+1}:")
            print(f"  路徑: {img_info['image_path']}")
            print(f"  說明: {img_info['description']}")
            print(f"  文章標題: {img_info['article_title'][:50]}...")
            print(f"  類別: {img_info['category']}")
            print(f"  新生成: {img_info['generated']}")
    
    print(f"\n✅ 完成！請檢查 {output_dir} 資料夾中的圖片和 image_metadata.json 檔案")

if __name__ == "__main__":
    main()
