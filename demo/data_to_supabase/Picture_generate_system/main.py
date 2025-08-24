import os
import json
from generate_picture import generate_from_json
from config import Config

def generate_images(
    input_json: str = None,
    output_dir: str = None,
    model_id: str = None,
    max_items: int = None,
    max_images_per_article: int = None,
    retry_times: int = None,
    sleep_between_calls: float = None
) -> dict:
    """
    使用設定生成圖片的主要函數
    
    Args:
        input_json: 輸入的JSON檔案路徑，如果不指定則使用Config中的設定
        output_dir: 輸出目錄路徑，如果不指定則使用Config中的設定
        model_id: AI模型ID，如果不指定則使用Config中的設定
        max_items: 處理文章數量限制，如果不指定則使用Config中的設定
        max_images_per_article: 每篇文章生成圖片數，如果不指定則使用Config中的設定
        retry_times: 重試次數，如果不指定則使用Config中的設定
        sleep_between_calls: API呼叫間隔，如果不指定則使用Config中的設定
    
    Returns:
        dict: 包含執行結果的字典
    """
    # 使用參數或配置檔中的設定
    input_json = input_json or Config.get_input_file_path()
    output_dir = output_dir or Config.get_output_dir_path()
    model_id = model_id or Config.MODEL_ID
    max_items = max_items if max_items is not None else Config.MAX_ITEMS
    max_images_per_article = max_images_per_article or Config.MAX_IMAGES_PER_ARTICLE
    retry_times = retry_times or Config.RETRY_TIMES
    sleep_between_calls = sleep_between_calls or Config.SLEEP_BETWEEN_CALLS
    
    return generate_from_json(
        input_json=input_json,
        output_dir=output_dir,
        model_id=model_id,
        max_items=max_items,
        max_images_per_article=max_images_per_article,
        retry_times=retry_times,
        sleep_between_calls=sleep_between_calls,
    )

def main():
    """主函數 - 生成圖片並建立說明文字"""
    
    # 使用配置檔案中的設定
    input_json = Config.get_input_file_path()
    output_dir = Config.get_output_dir_path()
    
    print("🎯 開始執行圖片生成與說明建立...")
    print(f"📁 輸入檔案: {input_json}")
    print(f"📁 輸出目錄: {output_dir}")
    
    # 檢查輸入檔案是否存在
    if not os.path.exists(input_json):
        print(f"❌ 錯誤：找不到輸入檔案 {input_json}")
        return
    
    # 執行圖片生成（包含說明功能）
    try:
        result = generate_from_json(
            input_json=input_json,
            output_dir=output_dir,
            # 使用配置檔中的設定
            model_id=Config.MODEL_ID,
            max_items=Config.MAX_ITEMS,
            max_images_per_article=Config.MAX_IMAGES_PER_ARTICLE,
            retry_times=Config.RETRY_TIMES,
            sleep_between_calls=Config.SLEEP_BETWEEN_CALLS,
        )
        
        # 顯示執行結果
        print("\n" + "="*50)
        print("🎉 執行完成！結果統計：")
        print("="*50)
        print(f"📊 處理文章數: {result['processed']}")
        print(f"✅ 成功生成: {result['succeeded']}")
        print(f"❌ 失敗數量: {result['failed']}")
        print(f"⚠️  錯誤數量: {result['errors_count']}")
        print(f"🖼️  總圖片數: {result['total_images']}")
        print(f"📁 輸出目錄: {result['output_dir']}")
        
        # 檢查並顯示 metadata 檔案資訊
        if 'metadata_path' in result and os.path.exists(result['metadata_path']):
            print(f"📋 Metadata檔案: {result['metadata_path']}")
            
            # 讀取並顯示部分 metadata 內容
            try:
                with open(result['metadata_path'], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                print("\n📝 圖片說明範例:")
                for i, img_info in enumerate(metadata['images'][:3]):  # 顯示前3個
                    print(f"\n  圖片 {i+1}:")
                    print(f"    📄 檔名: {os.path.basename(img_info['image_path'])}")
                    print(f"    💬 說明: {img_info['description']}")
                    print(f"    📰 文章: {img_info['article_title'][:50]}...")
                    print(f"    🏷️  類別: {img_info['category']}")
                
                if len(metadata['images']) > 3:
                    print(f"\n    ... 還有 {len(metadata['images']) - 3} 張圖片")
                    
            except Exception as e:
                print(f"⚠️  讀取 metadata 檔案時發生錯誤: {e}")
        
        # 檢查錯誤檔案
        if result['errors_count'] > 0:
            error_file = os.path.join(result['output_dir'], "errors.json")
            if os.path.exists(error_file):
                print(f"\n⚠️  發現錯誤記錄檔案: {error_file}")
                print("   請檢查該檔案了解詳細錯誤資訊")
        
        print("\n" + "="*50)
        print("✅ 所有任務完成！")
        print("📁 請檢查輸出目錄中的圖片檔案和 image_metadata.json")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        print("請檢查：")
        print("1. GEMINI_API_KEY 環境變數是否正確設定")
        print("2. 網路連線是否正常")
        print("3. 輸入檔案格式是否正確")

if __name__ == "__main__":
    main()
