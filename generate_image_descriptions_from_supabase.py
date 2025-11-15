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
            prompt = f"""請根據以下新聞內容和圖片，生成一個簡短且語意完整的圖片說明。

新聞內容：
{news_content[:1000]}

【絕對嚴格的要求 - 必須100%遵守】：

1. 字數限制：說明必須在 15 個字以內（含標點符號）
2. 完整性要求：說明必須是完整的句子，絕對不可以中途截斷
3. 標點符號：不要以逗號（，）、頓號（、）、分號（；）、冒號（：）結尾
4. 可接受的結尾：句號（。）、驚嘆號（！）、問號（？）或直接以名詞/動詞結尾
5. 禁止使用：「...」、「等」、「之類」等任何省略表達
6. 內容準確：必須準確描述圖片實際內容
7. 相關性：必須與新聞內容相關
8. 語氣：客觀、中立、不帶情感色彩
9. 格式：直接輸出說明文字，不要有任何前綴或說明
10. 精簡原則：在字數限制內，用最精煉的方式表達完整意思

【正確範例】（完整且符合字數）：
✓ 總統參加經濟論壇
✓ 股市今日收盤上漲
✓ 新手機產品發表
✓ 民眾街頭示威遊行
✓ 颱風造成淹水災情
✓ 新遊戲即將上市
✓ 遊戲發表會現場

【錯誤範例】（會被系統拒絕）：
✗ 總統出席重要的國際經濟會議並發表... (超過15字且被截斷)
✗ 股市收盤創下史上最高, (以逗號結尾)
✗ 新款科技產品等 (使用「等」省略)
✗ 民眾參與 (語意不完整)
✗ 《邊緣禁地4》2025年9月上市 (包含具體日期太長，應改為「新遊戲即將上市」)
✗ 退休金改革：法國政府面臨嚴峻挑戰 (應改為「退休金改革面臨挑戰」)

【重要提醒】：
- 如果原本想表達的內容會超過 15 字，請重新組織語句，用更精簡的方式表達完整意思
- 寧可犧牲細節，也要保證句子的完整性
- 每個字都要有意義，避免冗詞贅字

現在請生成符合所有要求的圖片說明：
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
            
            # 移除可能的引號或多餘空白
            description = description.strip('"\'「」『』 ')
            
            # 檢查長度
            if len(description) > 15:
                print(f"⚠️  警告：AI 生成的說明超過 15 字（{len(description)} 字）：{description}")
                print("   正在智能分析並修正...")
                
                # 定義一個函數來檢查縮寫是否會造成語意失真
                def is_meaningful_truncation(original: str, truncated: str) -> bool:
                    """檢查截斷後的內容是否仍保有完整語意，不會造成誤導"""
                    # 檢查1: 是否截斷了重要的時間、數字、地點等關鍵資訊的一半
                    # 例如："2025年9月" 被截成 "2025年" 就會失真
                    if '年' in truncated and '月' in original and '月' not in truncated:
                        # 有年但缺月，可能失真
                        if original.find('年') < original.find('月'):
                            return False
                    
                    # 檢查2: 是否截斷在數字中間（例如：2025年9 → 不完整）
                    if truncated and truncated[-1].isdigit():
                        # 找到原文中這個數字的完整範圍
                        truncated_end = len(truncated) - 1
                        if truncated_end < len(original) - 1 and original[truncated_end + 1].isdigit():
                            return False  # 數字被截斷
                    
                    # 檢查3: 是否以「於」、「在」、「將」等介詞或助詞結尾（表示後面還有資訊）
                    incomplete_endings = ['於', '在', '將', '至', '從', '向', '對', '為', '給', '被', '把']
                    if truncated and truncated[-1] in incomplete_endings:
                        return False
                    
                    # 檢查4: 是否包含書名號、引號但沒有閉合
                    quote_pairs = [
                        ('《', '》'), ('「', '」'), ('『', '』'), 
                        ('"', '"'), (''', '''), ('(', ')'), ('（', '）'), ('[', ']')
                    ]
                    for open_q, close_q in quote_pairs:
                        if open_q in truncated and close_q not in truncated:
                            return False  # 引號未閉合
                    
                    # 檢查5: 基本長度檢查 - 太短可能失去意義
                    if len(truncated) < 5:
                        return False
                    
                    return True
                
                # 策略1: 優先在句號、驚嘆號、問號處截斷（完整句子）
                best_cut = -1
                for i in range(14, 0, -1):
                    if description[i] in '。！？':
                        candidate = description[:i+1]
                        if is_meaningful_truncation(description, candidate):
                            best_cut = i + 1
                            break
                
                if best_cut > 0:
                    description = description[:best_cut]
                    print("   → 策略1：在句號處截斷為完整句子")
                else:
                    # 策略2: 智能分析語意結構
                    # 檢查是否有冒號（通常表示後面有解釋或列舉）
                    has_colon = '：' in description or ':' in description
                    
                    # 如果有冒號且在15字內，不適合截斷（會造成語意不完整）
                    if has_colon:
                        colon_pos = description.find('：')
                        if colon_pos == -1:
                            colon_pos = description.find(':')
                        
                        # 如果冒號在前半部，說明後面是重點，但前面可能有關鍵主題
                        if colon_pos < 10:
                            print("   → 偵測到冒號結構，分析最佳處理方式...")
                            
                            before_colon = description[:colon_pos].strip()
                            after_colon = description[colon_pos+1:].strip()
                            
                            # 策略2A: 嘗試結合主題和重點（如果能放進15字內）
                            # 提取冒號前的關鍵詞（主題）
                            subject_keywords = before_colon.split()[-2:] if len(before_colon.split()) >= 2 else [before_colon]
                            subject = ''.join(subject_keywords)
                            
                            # 嘗試組合：主題 + 簡化的重點
                            combined_options = []
                            
                            # 選項1: 主題 + 冒號後內容（去掉句號）
                            option1 = f"{subject}{after_colon.rstrip('。！？')}"
                            if len(option1) <= 15:
                                combined_options.append(('option1', option1, '保留主題和重點'))
                            
                            # 選項2: 主題 + 動詞片段（如果冒號後有逗號，取第一部分）
                            if '，' in after_colon or '、' in after_colon:
                                first_part = after_colon.split('，')[0].split('、')[0].strip()
                                option2 = f"{subject}{first_part}"
                                if len(option2) <= 15 and len(option2) >= 5:
                                    combined_options.append(('option2', option2, '主題+第一重點'))
                            
                            # 選項3: 只取冒號後內容（如果夠精準）
                            if len(after_colon) <= 15 and len(after_colon) >= 5:
                                combined_options.append(('option3', after_colon, '只保留重點部分'))
                            
                            # 評估選項：優先選擇包含主題的
                            best_option = None
                            for opt_name, opt_text, opt_desc in combined_options:
                                if is_meaningful_truncation(description, opt_text):
                                    # 檢查是否保留了主題資訊
                                    has_subject = any(word in opt_text for word in before_colon[:6])
                                    if has_subject:
                                        best_option = (opt_text, f"策略2A-{opt_name}: {opt_desc}（保留主題）")
                                        break
                            
                            # 如果沒有包含主題的，退而求其次選不失真的
                            if not best_option:
                                for opt_name, opt_text, opt_desc in combined_options:
                                    if is_meaningful_truncation(description, opt_text):
                                        best_option = (opt_text, f"策略2A-{opt_name}: {opt_desc}")
                                        break
                            
                            if best_option:
                                description, reason = best_option
                                print(f"   → {reason}")
                            else:
                                # 所有選項都不合適，使用備用說明
                                description = None
                                print("   → 策略2 失敗：無法找到精準且不失真的表達")
                        
                        # 如果策略2失敗，使用備用說明
                        if description is None:
                            # 生成簡短的備用說明（確保不超過15字）
                            category_map = {
                                '政治': '政治新聞',
                                '經濟': '經濟新聞',
                                '社會': '社會新聞',
                                '國際': '國際新聞',
                                '科技': '科技新聞',
                                '體育': '體育新聞',
                                '娛樂': '娛樂新聞',
                                'Science & Technology': '科技新聞',
                                'Technology': '科技新聞',
                                'Business': '商業新聞',
                                'Sports': '體育新聞',
                                'Entertainment': '娛樂新聞'
                            }
                            description = category_map.get(category, '新聞圖片')
                            print(f"   → 使用備用說明：{description}")
                    
                    # 策略3: 在逗號、頓號處尋找語意完整的片段
                    if len(description) > 15:  # 如果還是太長
                        candidates = []
                        original_desc = description
                        for i in range(min(14, len(description)-1), 4, -1):
                            if description[i] in '，、':
                                candidate = description[:i]
                                # 檢查結尾是否完整（不以助詞、冒號結尾）
                                if candidate and candidate[-1] not in '的了在與和及或：:':
                                    # 驗證語意是否失真
                                    if is_meaningful_truncation(original_desc, candidate):
                                        candidates.append((i, candidate))
                        
                        if candidates:
                            best_idx, description = candidates[0]
                            print("   → 策略3：在標點處取語意完整部分")
                        else:
                            print("   → 策略3 失敗：找不到不失真的截斷點")
                            
                            # 策略4: 檢查是否仍需處理
                            if len(description) > 15:
                                # 使用簡短備用說明，避免失真
                                print("   → 無法在不失真的情況下縮短，使用備用說明")
                                category_map = {
                                    '政治': '政治新聞',
                                    '經濟': '經濟新聞',
                                    '社會': '社會新聞',
                                    '國際': '國際新聞',
                                    '科技': '科技新聞',
                                    '體育': '體育新聞',
                                    '娛樂': '娛樂新聞',
                                    'Science & Technology': '科技新聞',
                                    'Technology': '科技新聞',
                                    'Business': '商業新聞',
                                    'Sports': '體育新聞',
                                    'Entertainment': '娛樂新聞'
                                }
                                description = category_map.get(category, '新聞圖片')
                
                print(f"   ✓ 最終結果：{description} ({len(description)}字)")
            
            # 最終清理：確保不以不適當的標點結尾
            while description and description[-1] in '，、；：':
                description = description[:-1]
            
            # 確保不是空字串且有實際內容
            if not description or len(description) < 3:
                print("⚠️  生成的說明過短或為空，使用備用說明")
                description = f"{category}新聞圖片" if category else "新聞圖片"
            
            # 最終驗證
            if len(description) > 15:
                print("❌ 錯誤：截斷後仍超過 15 字，強制截斷")
                description = description[:15].rstrip('的了在與和，、；：及或是有到被給為著過')
            
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
