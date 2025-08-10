#!/usr/bin/env python3
"""
檢查生成結果的簡單腳本
"""

import os
import json

def check_results():
    output_dir = "generated_images_with_descriptions"
    metadata_file = os.path.join(output_dir, "image_metadata.json")
    
    print(f"檢查輸出目錄: {output_dir}")
    
    if not os.path.exists(output_dir):
        print("❌ 輸出目錄不存在")
        return
    
    # 列出所有子目錄
    subdirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    print(f"✅ 找到 {len(subdirs)} 個類別資料夾: {subdirs}")
    
    # 統計圖片數量
    total_images = 0
    for subdir in subdirs:
        subdir_path = os.path.join(output_dir, subdir)
        images = [f for f in os.listdir(subdir_path) if f.endswith('.png')]
        total_images += len(images)
        print(f"  {subdir}: {len(images)} 張圖片")
    
    print(f"📊 總計: {total_images} 張圖片")
    
    # 檢查metadata檔案
    if os.path.exists(metadata_file):
        print(f"✅ 找到metadata檔案: {metadata_file}")
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"📋 Metadata統計:")
            print(f"  總圖片數: {metadata.get('total_images', 0)}")
            print(f"  生成時間: {metadata.get('generated_at', 'N/A')}")
            
            # 顯示前幾個範例
            if 'images' in metadata and metadata['images']:
                print(f"\n📝 說明範例:")
                for i, img_info in enumerate(metadata['images'][:3]):
                    print(f"\n  圖片 {i+1}:")
                    print(f"    檔名: {os.path.basename(img_info.get('image_path', ''))}")
                    print(f"    說明: {img_info.get('description', '')}")
                    print(f"    類別: {img_info.get('category', '')}")
                    print(f"    新生成: {img_info.get('generated', False)}")
                    
        except Exception as e:
            print(f"❌ 讀取metadata檔案時發生錯誤: {e}")
    else:
        print(f"⚠️  未找到metadata檔案: {metadata_file}")
    
    # 檢查錯誤檔案
    error_file = os.path.join(output_dir, "errors.json")
    if os.path.exists(error_file):
        print(f"⚠️  發現錯誤檔案: {error_file}")
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)
            print(f"  錯誤數量: {len(errors)}")
        except:
            print("  無法讀取錯誤檔案")
    else:
        print("✅ 沒有錯誤檔案")

if __name__ == "__main__":
    check_results()
