#!/usr/bin/env python3
"""
簡潔版圖片生成主程式 - 使用配置檔案
"""

import os
from config import (
    INPUT_JSON, OUTPUT_DIR, MODEL_ID, MAX_ITEMS, 
    MAX_IMAGES_PER_ARTICLE, RETRY_TIMES, SLEEP_BETWEEN_CALLS
)
from generate_picture import generate_from_json

def main():
    """簡潔的主函數"""
    
    print(f"開始生成圖片: {INPUT_JSON} -> {OUTPUT_DIR}")
    
    # 檢查輸入檔案
    if not os.path.exists(INPUT_JSON):
        print(f"錯誤：找不到 {INPUT_JSON}")
        return
    
    # 執行圖片生成
    result = generate_from_json(
        input_json=INPUT_JSON,
        output_dir=OUTPUT_DIR,
        model_id=MODEL_ID,
        max_items=MAX_ITEMS,
        max_images_per_article=MAX_IMAGES_PER_ARTICLE,
        retry_times=RETRY_TIMES,
        sleep_between_calls=SLEEP_BETWEEN_CALLS,
    )
    
    # 簡潔的結果顯示
    print(f"完成: {result['succeeded']}/{result['processed']} 成功")
    print(f"圖片: {result['total_images']} 張")
    print(f"目錄: {result['output_dir']}")
    
    if 'metadata_path' in result:
        print(f"說明: {result['metadata_path']}")
    
    if result['errors_count'] > 0:
        print(f"錯誤: {result['errors_count']} 個")

if __name__ == "__main__":
    main()
