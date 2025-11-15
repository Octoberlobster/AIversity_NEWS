#!/usr/bin/env python3
"""
從 Supabase generated_image 表讀取圖片，結合 single_news 內容生成圖片說明
並更新回 description 欄位
"""

import os
import base64  # noqa: F401 - used in decode_base64_image
import time
import argparse
from typing import Dict, Any, List, Optional
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 檢查必要的環境變數
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError('請在 .env 檔案中設定 SUPABASE_URL 和 SUPABASE_KEY')

if not GEMINI_API_KEY:
    raise EnvironmentError('請在 .env 檔案中設定 GEMINI_API_KEY 或 GOOGLE_API_KEY')

# 導入必要的套件
try:
    from supabase import create_client
    print("✓ Supabase 套件已載入")
except ImportError:
    raise ImportError("請先安裝 supabase-py：pip install supabase")

try:
    from google import genai
    from google.genai import types
    print("✓ Google Genai 套件已載入")
except ImportError:
    raise ImportError("請先安裝 google-genai：pip install google-genai")


class ImageDescriptionGenerator:
    """圖片說明生成器"""
    
    def __init__(self, dry_run: bool = False):
        """初始化 Supabase 和 Gemini 客戶端
        
        Args:
            dry_run: 如果為 True，則不會實際寫入資料庫
        """
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash"  # 支援 vision 的模型
        self.dry_run = dry_run
        
    def fetch_generated_images(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        從 Supabase 讀取 generated_image 表的資料
        
        Args:
            limit: 限制讀取的筆數，None 表示讀取全部
            
        Returns:
            List[Dict]: 圖片資料列表
        """
        print("正在讀取 generated_image 表...")
        
        query = self.supabase.table("generated_image").select("*")
        print(query)
        
        if limit:
            query = query.limit(limit)
            
        response = query.execute()
        
        if response.data:
            print(f"✓ 成功讀取 {len(response.data)} 筆圖片資料")
            return response.data
        else:
            print("⚠ 沒有找到圖片資料")
            return []
    
    def fetch_news_by_story_id(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        根據 story_id 從 single_news 表讀取新聞內容
        
        Args:
            story_id: 新聞故事 ID
            
        Returns:
            Dict: 新聞資料，包含 long 欄位
        """
        try:
            response = self.supabase.table("single_news").select("*").eq("story_id", story_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                print(f"⚠ 找不到 story_id={story_id} 的新聞")
                return None
        except Exception as e:
            print(f"❌ 讀取新聞時發生錯誤: {e}")
            return None
    
    def decode_base64_image(self, base64_str: str) -> Optional[Image.Image]:
        """
        將 base64 字串解碼為 PIL Image
        
        Args:
            base64_str: base64 編碼的圖片字串
            
        Returns:
            PIL.Image: 解碼後的圖片物件
        """
        try:
            # 移除可能的 data URL 前綴
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            
            # 解碼 base64
            image_bytes = base64.b64decode(base64_str)
            image = Image.open(BytesIO(image_bytes))
            
            return image
        except Exception as e:
            print(f"❌ 解碼圖片時發生錯誤: {e}")
            return None
    
    def generate_description_with_vision(
        self, 
        image: Image.Image, 
        news_content: str,
        category: str = ""
    ) -> str:
        """
        使用 Gemini Vision API 分析圖片並結合新聞內容生成說明
        
        Args:
            image: PIL Image 物件
            news_content: 新聞內容
            category: 新聞類別
            
        Returns:
            str: 生成的圖片說明（15字以內）
        """
        try:
            # 將圖片轉換為 bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # 建立提示詞
            prompt = f"""請根據以下新聞內容和圖片，生成一個簡短完整的圖片說明。

新聞內容：
{news_content[:500]}

嚴格要求：
1. 說明必須是完整的句子，不可以中途截斷
2. 說明字數必須在 15 個字以內（包含標點符號）
3. 如果超過 15 字，請縮短句子但必須保持完整性
4. 必須準確描述圖片內容
5. 必須與新聞內容相關
6. 使用客觀、中立的語氣
7. 直接輸出說明文字，不要有任何前綴或後綴
8. 不要使用「...」或「等」等省略符號

正確範例：
- 總統出席國際會議
- 股市收盤創新高
- 新款手機發表會
- 民眾參與遊行活動

錯誤範例（會被截斷）：
- 總統出席重要的國際經濟... (X - 不完整)
- 股市收盤創下史上最高記... (X - 被截斷)

請確保生成的說明是一個語意完整、不會被截斷的句子。
"""
            
            # 使用 Gemini Vision API
            response = self.genai_client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=img_bytes,
                                mime_type="image/png"
                            ),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ]
            )
            
            # 提取生成的文字
            description = response.text.strip()
            
            # 智能截斷：確保是完整句子
            if len(description) > 15:
                # 嘗試在標點符號處截斷
                for i in range(14, 0, -1):
                    if description[i] in '。！？，、；：':
                        description = description[:i+1]
                        break
                else:
                    # 如果沒有找到標點符號，在最後一個完整詞處截斷
                    # 避免截斷到詞的中間
                    description = description[:15]
                    # 移除可能的不完整標點
                    while description and description[-1] in '的了在與和':
                        description = description[:-1]
            
            # 確保不是空字串
            if not description:
                description = f"{category}新聞圖片" if category else "新聞圖片"
            
            return description
            
        except Exception as e:
            print(f"❌ 生成說明時發生錯誤: {e}")
            # 使用備用說明
            return f"{category}相關新聞圖片" if category else "新聞相關圖片"
    
    def update_description(self, image_id: int, description: str) -> bool:
        """
        更新 generated_image 表的 description 欄位
        
        Args:
            image_id: 圖片記錄的 ID
            description: 新的說明文字
            
        Returns:
            bool: 更新是否成功
        """
        if self.dry_run:
            print("🔍 [測試模式] 不會實際寫入資料庫")
            return True
            
        try:
            self.supabase.table("generated_image").update({
                "description": description
            }).eq("id", image_id).execute()
            
            return True
        except Exception as e:
            print(f"❌ 更新說明時發生錯誤: {e}")
            return False
    
    def process_images(self, limit: Optional[int] = None, sleep_time: float = 1.0):
        """
        處理所有圖片：讀取、生成說明、更新
        
        Args:
            limit: 限制處理的圖片數量
            sleep_time: 每次 API 呼叫之間的等待時間（秒）
        """
        print("\n" + "="*60)
        if self.dry_run:
            print("🔍 測試模式 - 不會實際寫入資料庫")
        print("開始處理圖片說明生成")
        print("="*60 + "\n")
        
        # 讀取圖片資料
        images = self.fetch_generated_images(limit)
        
        if not images:
            print("沒有圖片需要處理")
            return
        
        # 統計資訊
        total = len(images)
        success = 0
        failed = 0
        skipped = 0
        
        # 處理每張圖片
        for idx, image_record in enumerate(images, 1):
            print(f"\n處理進度: {idx}/{total}")
            print("-" * 60)
            
            image_id = image_record.get('id')
            story_id = image_record.get('story_id')
            image_base64 = image_record.get('image')
            current_description = image_record.get('description', '')
            
            print(f"圖片 ID: {image_id}")
            print(f"Story ID: {story_id}")
            print(f"目前說明: {current_description}")
            
            # 如果已經有說明且不為空，可以選擇跳過
            # 如果要重新生成所有說明，請註解掉下面這段
            # if current_description and current_description.strip():
            #     print("⏭ 已有說明，跳過")
            #     skipped += 1
            #     continue
            
            # 檢查必要欄位
            if not image_base64:
                print("⚠ 圖片資料為空，跳過")
                skipped += 1
                continue
            
            if not story_id:
                print("⚠ story_id 為空，跳過")
                skipped += 1
                continue
            
            # 1. 解碼圖片
            print("正在解碼圖片...")
            image = self.decode_base64_image(image_base64)
            
            if not image:
                print("❌ 圖片解碼失敗")
                failed += 1
                continue
            
            print(f"✓ 圖片解碼成功 ({image.size[0]}x{image.size[1]})")
            
            # 2. 讀取新聞內容
            print(f"正在讀取 story_id={story_id} 的新聞...")
            news = self.fetch_news_by_story_id(story_id)
            
            if not news:
                print("❌ 無法讀取新聞內容")
                failed += 1
                continue
            
            news_long = news.get('long', '')
            category = news.get('category', '')
            
            print(f"✓ 新聞內容長度: {len(news_long)} 字")
            print(f"類別: {category}")
            
            # 3. 生成說明
            print("正在生成圖片說明...")
            description = self.generate_description_with_vision(
                image=image,
                news_content=news_long,
                category=category
            )
            
            print(f"✓ 生成說明: {description}")
            
            # 4. 更新資料庫
            print("正在更新資料庫...")
            if self.update_description(image_id, description):
                print(f"✅ 成功更新圖片 {image_id} 的說明")
                success += 1
            else:
                print("❌ 更新失敗")
                failed += 1
            
            # API 節流
            if idx < total:
                print(f"等待 {sleep_time} 秒...")
                time.sleep(sleep_time)
        
        # 顯示統計結果
        print("\n" + "="*60)
        print("處理完成")
        print("="*60)
        print(f"總計: {total}")
        print(f"成功: {success}")
        print(f"失敗: {failed}")
        print(f"跳過: {skipped}")
        print("="*60 + "\n")


def main():
    """主函數"""
    
    # 設定命令列參數
    parser = argparse.ArgumentParser(
        description='從 Supabase 生成圖片說明並更新資料庫',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用範例:
  python generate_image_descriptions_from_supabase.py
  python generate_image_descriptions_from_supabase.py --no-write
  python generate_image_descriptions_from_supabase.py --limit 10
  python generate_image_descriptions_from_supabase.py --no-write --limit 5 --sleep 3.0
        """
    )
    
    parser.add_argument(
        '--no-write',
        action='store_true',
        help='測試模式：不會實際寫入資料庫，只顯示會生成的說明'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制處理的圖片數量（預設：處理全部）'
    )
    
    parser.add_argument(
        '--sleep',
        type=float,
        default=2.0,
        help='API 呼叫之間的等待時間（秒，預設：2.0）'
    )
    
    args = parser.parse_args()
    
    print("\n圖片說明生成器")
    print("從 Supabase generated_image 表讀取圖片並生成說明\n")
    
    if args.no_write:
        print("⚠️  測試模式啟用 - 不會實際寫入資料庫")
        print("   若要實際更新資料庫，請移除 --no-write 參數\n")
    
    # 初始化生成器
    generator = ImageDescriptionGenerator(dry_run=args.no_write)
    
    # 執行處理
    try:
        generator.process_images(limit=args.limit, sleep_time=args.sleep)
    except KeyboardInterrupt:
        print("\n\n⚠ 使用者中斷執行")
    except Exception as e:
        print(f"\n\n❌ 執行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
