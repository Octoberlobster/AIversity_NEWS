#!/usr/bin/env python3
"""
從 Supabase generated_image 表讀取圖片，結合 single_news 內容生成圖片說明
並更新回 description 欄位
"""

import os
import base64  # noqa: F401 - used in decode_base64_image
import time
import argparse
import json
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
    
    def validate_description(self, description: str) -> Dict[str, Any]:
        """
        檢查圖片說明是否符合標準
        
        檢查項目：
        1. 字數限制（15字以內含標點）
        2. 不可以中途截斷（不以逗號、頓號、分號、冒號結尾）
        3. 不可使用省略表達（...、等、之類）
        4. 不可為空或過短（至少3字）
        5. 不以助詞結尾（的、了、在、與、和等）
        
        Args:
            description: 要檢查的說明文字
            
        Returns:
            Dict: {
                'valid': bool,  # 是否符合標準
                'length': int,  # 字數
                'errors': List[str],  # 錯誤訊息列表
                'warnings': List[str]  # 警告訊息列表
            }
        """
        errors = []
        warnings = []
        
        # 檢查1: 空值或過短
        if not description or not description.strip():
            errors.append("說明為空")
            return {
                'valid': False,
                'length': 0,
                'errors': errors,
                'warnings': warnings
            }
        
        description = description.strip()
        length = len(description)
        
        # 檢查2: 字數限制
        if length > 15:
            errors.append(f"超過15字限制（目前{length}字）")
        
        if length < 3:
            errors.append(f"說明過短（目前{length}字），至少需要3字")
        
        # 檢查3: 不當的結尾標點
        invalid_endings = ['，', '、', '；', '：', ':']
        if description[-1] in invalid_endings:
            errors.append(f"不應以「{description[-1]}」結尾（表示語意未完成）")
        
        # 檢查4: 省略表達
        ellipsis_patterns = ['...', '……', '等', '之類', '等等']
        for pattern in ellipsis_patterns:
            if pattern in description:
                errors.append(f"包含省略表達「{pattern}」")
        
        # 檢查5: 不應以助詞結尾
        weak_endings = ['的', '了', '在', '與', '和', '及', '或', '是', '有', '到', '被', '給', '為', '著', '過']
        if description[-1] in weak_endings:
            warnings.append(f"以助詞「{description[-1]}」結尾（建議調整）")
        
        # 檢查6: 引號未閉合
        quote_pairs = [
            ('《', '》'), ('「', '」'), ('『', '』'), 
            ('"', '"'), (''', '''), ('(', ')'), ('（', '）'), ('[', ']')
        ]
        for open_q, close_q in quote_pairs:
            if open_q in description and close_q not in description:
                errors.append(f"引號未閉合：{open_q} 缺少對應的 {close_q}")
        
        # 檢查7: 數字截斷（例如：2025年 後面應該有月份但被截斷）
        if '年' in description and description.endswith(('年', '年1', '年2', '年3', '年4', '年5', '年6', '年7', '年8', '年9', '年0')):
            # 檢查是否看起來像年份被截斷
            year_pos = description.rfind('年')
            if year_pos == len(description) - 1:  # 以「年」結尾
                warnings.append("可能缺少月份資訊（只有年份）")
        
        # 判斷是否有效
        valid = len(errors) == 0
        
        return {
            'valid': valid,
            'length': length,
            'errors': errors,
            'warnings': warnings
        }
    
    def check_all_descriptions(self, limit: Optional[int] = None, show_valid: bool = False) -> Dict[str, Any]:
        """
        檢查所有已生成的圖片說明是否符合標準
        
        Args:
            limit: 限制檢查的圖片數量
            show_valid: 是否顯示符合標準的說明（預設只顯示有問題的）
            
        Returns:
            Dict: 統計資訊
        """
        print("\n" + "="*60)
        print("檢查已生成的圖片說明")
        print("="*60 + "\n")
        
        # 讀取圖片資料
        images = self.fetch_generated_images(limit)
        
        if not images:
            print("沒有圖片資料")
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'empty': 0
            }
        
        # 統計資訊
        total = len(images)
        valid_count = 0
        invalid_count = 0
        empty_count = 0
        
        invalid_records = []
        
        print(f"開始檢查 {total} 筆圖片說明...\n")
        
        # 檢查每筆資料
        for idx, image_record in enumerate(images, 1):
            image_id = image_record.get('id')
            story_id = image_record.get('story_id')
            description = image_record.get('description', '')
            
            # 執行驗證
            validation_result = self.validate_description(description)
            
            if not description or not description.strip():
                empty_count += 1
                print(f"[{idx}/{total}] ID:{image_id} | Story:{story_id}")
                print(f"  ⚠️  說明為空")
                print()
                invalid_records.append({
                    'id': image_id,
                    'story_id': story_id,
                    'description': description,
                    'validation': validation_result
                })
            elif validation_result['valid']:
                valid_count += 1
                if show_valid:
                    print(f"[{idx}/{total}] ID:{image_id} | Story:{story_id}")
                    print(f"  ✅ 符合標準: {description} ({validation_result['length']}字)")
                    if validation_result['warnings']:
                        for warning in validation_result['warnings']:
                            print(f"    ⚠️  警告: {warning}")
                    print()
            else:
                invalid_count += 1
                print(f"[{idx}/{total}] ID:{image_id} | Story:{story_id}")
                print(f"  ❌ 不符合標準: {description} ({validation_result['length']}字)")
                for error in validation_result['errors']:
                    print(f"    • 錯誤: {error}")
                for warning in validation_result['warnings']:
                    print(f"    • 警告: {warning}")
                print()
                
                invalid_records.append({
                    'id': image_id,
                    'story_id': story_id,
                    'description': description,
                    'validation': validation_result
                })
        
        # 顯示統計結果
        print("="*60)
        print("檢查結果統計")
        print("="*60)
        print(f"總計:           {total}")
        print(f"✅ 符合標準:    {valid_count} ({valid_count/total*100:.1f}%)")
        print(f"❌ 不符合標準:  {invalid_count} ({invalid_count/total*100:.1f}%)")
        print(f"⚠️  說明為空:    {empty_count} ({empty_count/total*100:.1f}%)")
        print("="*60 + "\n")
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': invalid_count,
            'empty': empty_count,
            'invalid_records': invalid_records
        }
    
    def update_all_descriptions(self, limit: Optional[int] = None, update_limit: Optional[int] = None, sleep_time: float = 2.0):
        """
        批量更新圖片說明（逐筆處理，處理完立即更新）
        
        Args:
            limit: 限制檢查的圖片數量（從資料庫讀取的總數）
            update_limit: 限制實際更新的數量（處理的最大筆數）
            sleep_time: 每次 API 呼叫之間的等待時間（秒）
        """
        print("\n" + "="*60)
        if self.dry_run:
            print("🔍 測試模式 - 不會實際寫入資料庫")
        print("批量更新圖片的多語言說明（逐筆處理模式）")
        print("="*60 + "\n")
        
        # 統計
        success = 0
        failed = 0
        skipped = 0
        processed = 0
        
        # 決定要處理的總數
        target_count = update_limit if update_limit else limit
        
        if target_count:
            print(f"目標：處理 {target_count} 筆圖片\n")
        else:
            print("目標：處理所有圖片\n")
        
        print("="*60 + "\n")
        
        # 逐筆讀取並處理
        batch_size = 10  # 每次讀取 10 筆
        start = 0
        
        while True:
            # 檢查是否已達到處理上限
            if target_count and processed >= target_count:
                print(f"\n✓ 已達到處理上限 {target_count} 筆")
                break
            
            # 讀取一批資料
            try:
                # 計算本批要讀取的數量
                remaining = (target_count - processed) if target_count else batch_size
                current_batch_size = min(batch_size, remaining) if target_count else batch_size
                
                end = start + current_batch_size - 1
                print(f"[讀取] 正在讀取第 {start} 到 {end} 筆...")
                
                response = self.supabase.table("generated_image").select("*").range(start, end).execute()
                
                if not response.data or len(response.data) == 0:
                    print("\n✓ 已處理完所有資料")
                    break
                
                images = response.data
                print(f"[讀取] ✓ 讀取到 {len(images)} 筆\n")
                
            except Exception as e:
                print(f"❌ 讀取資料時發生錯誤: {e}")
                break
            
            # 處理這批資料
            for image_record in images:
                processed += 1
                
                image_id = image_record.get('id')
                story_id = image_record.get('story_id')
                current_description = image_record.get('description', '')
                
                print(f"[{processed}] 正在處理 ID:{image_id}")
                print(f"  Story ID: {story_id}")
                print(f"  目前中文說明: {current_description}")
                
                # 檢查必要欄位
                image_base64 = image_record.get('image')
                if not image_base64:
                    print("  ⚠️  圖片資料為空，跳過")
                    skipped += 1
                    print()
                    continue
                
                if not story_id:
                    print("  ⚠️  story_id 為空，跳過")
                    skipped += 1
                    print()
                    continue
                
                # 解碼圖片
                print("  正在解碼圖片...")
                image = self.decode_base64_image(image_base64)
                if not image:
                    print("  ❌ 圖片解碼失敗")
                    failed += 1
                    print()
                    continue
                
                # 讀取新聞
                print(f"  正在讀取新聞 (story_id={story_id})...")
                news = self.fetch_news_by_story_id(story_id)
                if not news:
                    print("  ❌ 無法讀取新聞內容")
                    failed += 1
                    print()
                    continue
                
                # 生成多語言說明
                print("  🔄 生成多語言說明...")
                new_descriptions = self.generate_description_with_vision(
                    image=image,
                    news_content=news.get('long', ''),
                    category=news.get('category', '')
                )
                
                print("  ✓ 生成完成:")
                print(f"    中文: {new_descriptions['zh']}")
                print(f"    英文: {new_descriptions['en']}")
                print(f"    日文: {new_descriptions['ja']}")
                print(f"    印尼文: {new_descriptions['id']}")
                
                # 立即更新資料庫
                print("  正在更新資料庫...")
                if self.update_description(story_id, new_descriptions):
                    print("  ✅ 已更新多語言說明到資料庫")
                    success += 1
                else:
                    print("  ❌ 更新失敗")
                    failed += 1
                
                print()
                
                # 檢查是否已達到處理上限
                if target_count and processed >= target_count:
                    print(f"✓ 已達到處理上限 {target_count} 筆")
                    break
                
                # API 節流
                time.sleep(sleep_time)
            
            # 如果已達到處理上限，跳出外層循環
            if target_count and processed >= target_count:
                break
            
            # 移動到下一批
            start += batch_size
        
        # 顯示統計
        print("\n" + "="*60)
        print("更新完成")
        print("="*60)
        print(f"處理: {processed}")
        print(f"成功: {success}")
        print(f"失敗: {failed}")
        print(f"跳過: {skipped}")
        print("="*60 + "\n")
    
    def fix_invalid_descriptions(self, limit: Optional[int] = None, fix_limit: Optional[int] = None, sleep_time: float = 2.0):
        """
        修正不符合標準的圖片說明
        
        Args:
            limit: 限制檢查的圖片數量（從資料庫讀取的總數）
            fix_limit: 限制實際修正的數量（從不合格的項目中挑選）
            sleep_time: 每次 API 呼叫之間的等待時間（秒）
        """
        print("\n" + "="*60)
        if self.dry_run:
            print("🔍 測試模式 - 不會實際寫入資料庫")
        print("修正不符合標準的圖片說明")
        print("="*60 + "\n")
        
        # 先執行檢查
        check_result = self.check_all_descriptions(limit=limit, show_valid=False)
        
        if check_result['invalid'] == 0 and check_result['empty'] == 0:
            print("✅ 所有說明都符合標準，無需修正")
            return
        
        invalid_records = check_result['invalid_records']
        
        print(f"\n找到 {len(invalid_records)} 筆需要修正的記錄")
        
        # 如果設定了 fix_limit，只處理指定數量
        if fix_limit and fix_limit < len(invalid_records):
            print(f"⚠️  將只修正前 {fix_limit} 筆（使用 --fix-limit 參數限制）")
            invalid_records = invalid_records[:fix_limit]
        
        print("="*60 + "\n")
        
        # 統計
        success = 0
        failed = 0
        
        for idx, record in enumerate(invalid_records, 1):
            image_id = record['id']
            story_id = record['story_id']
            old_description = record['description']
            validation = record['validation']
            
            print(f"[{idx}/{len(invalid_records)}] 正在修正 ID:{image_id}")
            print(f"  原說明: {old_description}")
            print(f"  問題: {', '.join(validation['errors'])}")
            
            # 讀取圖片和新聞
            image_record = self.supabase.table("generated_image").select("*").eq("id", image_id).execute()
            if not image_record.data:
                print("  ❌ 無法讀取圖片資料")
                failed += 1
                continue
            
            image_base64 = image_record.data[0].get('image')
            if not image_base64:
                print("  ❌ 圖片資料為空")
                failed += 1
                continue
            
            # 解碼圖片
            image = self.decode_base64_image(image_base64)
            if not image:
                print("  ❌ 圖片解碼失敗")
                failed += 1
                continue
            
            # 讀取新聞
            news = self.fetch_news_by_story_id(story_id)
            if not news:
                print("  ❌ 無法讀取新聞內容")
                failed += 1
                continue
            
            # 重新生成多語言說明
            print("  🔄 重新生成多語言說明...")
            new_descriptions = self.generate_description_with_vision(
                image=image,
                news_content=news.get('long', ''),
                category=news.get('category', '')
            )
            
            # 驗證新的中文說明
            new_validation = self.validate_description(new_descriptions['zh'])
            
            print(f"  新說明:")
            print(f"    中文: {new_descriptions['zh']} ({new_validation['length']}字)")
            print(f"    英文: {new_descriptions['en']}")
            print(f"    日文: {new_descriptions['ja']}")
            print(f"    印尼文: {new_descriptions['id']}")
            
            if new_validation['valid']:
                print("  ✅ 新的中文說明符合標準")
                # 更新資料庫
                if self.update_description(story_id, new_descriptions):
                    print("  ✅ 已更新多語言說明到資料庫")
                    success += 1
                else:
                    print("  ❌ 更新失敗")
                    failed += 1
            else:
                print("  ⚠️  新的中文說明仍不符合標準:")
                for error in new_validation['errors']:
                    print(f"    • {error}")
                # 仍然更新（總比舊的好）
                if self.update_description(story_id, new_descriptions):
                    print("  ⚠️  已更新（但仍需人工檢查）")
                    success += 1
                else:
                    print("  ❌ 更新失敗")
                    failed += 1
            
            print()
            
            # API 節流
            if idx < len(invalid_records):
                time.sleep(sleep_time)
        
        # 顯示統計
        print("="*60)
        print("修正完成")
        print("="*60)
        print(f"需修正: {len(invalid_records)}")
        print(f"成功: {success}")
        print(f"失敗: {failed}")
        print("="*60 + "\n")
        
    def fetch_generated_images(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        從 Supabase 讀取 generated_image 表的資料（使用分批讀取避免逾時）
        
        Args:
            limit: 限制讀取的筆數，None 表示讀取全部
            
        Returns:
            List[Dict]: 圖片資料列表
        """
        print("正在讀取 generated_image 表...")
        
        all_data = []
        batch_size = 100  # 每批讀取 100 筆
        start = 0
        
        # 如果有限制，調整批次大小
        if limit and limit < batch_size:
            batch_size = limit
        
        while True:
            try:
                # 計算本批次要讀取的數量
                current_batch_size = batch_size
                if limit:
                    remaining = limit - len(all_data)
                    if remaining <= 0:
                        break
                    current_batch_size = min(batch_size, remaining)
                
                # 使用 range 分頁讀取
                end = start + current_batch_size - 1
                print(f"  正在讀取 {start} 到 {end}...")
                
                response = self.supabase.table("generated_image").select("*").range(start, end).execute()
                
                if not response.data or len(response.data) == 0:
                    # 沒有更多資料了
                    break
                
                all_data.extend(response.data)
                print(f"  ✓ 已讀取 {len(all_data)} 筆")
                
                # 如果這批資料少於批次大小，表示已經讀完
                if len(response.data) < current_batch_size:
                    break
                
                # 如果有限制且已達到限制
                if limit and len(all_data) >= limit:
                    break
                
                start += current_batch_size
                
                # 短暫延遲避免 API 限流
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = str(e)
                if 'statement timeout' in error_msg:
                    print(f"  ⚠️  資料庫逾時，嘗試減小批次大小...")
                    batch_size = max(10, batch_size // 2)  # 減半批次大小，最小 10
                    continue
                else:
                    print(f"  ❌ 讀取錯誤: {e}")
                    break
        
        if all_data:
            print(f"✓ 總共成功讀取 {len(all_data)} 筆圖片資料")
            return all_data
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
    ) -> Dict[str, str]:
        """
        使用 Gemini Vision API 分析圖片並結合新聞內容生成多語言說明
        
        Args:
            image: PIL Image 物件
            news_content: 新聞內容
            category: 新聞類別
            
        Returns:
            Dict[str, str]: 包含四種語言的圖片說明 {
                'zh': 中文說明,
                'en': 英文說明,
                'ja': 日文說明,
                'id': 印尼文說明
            }
        """
        try:
            # 將圖片轉換為 bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # 建立多語言提示詞
            prompt = f"""請根據以下新聞內容和圖片，生成四種語言的簡短圖片說明。

新聞內容：
{news_content[:1000]}

【絕對嚴格的要求 - 必須100%遵守】：

1. 字數限制：
   - 中文：15字以內（含標點符號）
   - 英文：12個單字以內
   - 日文：15字以內（含標點符號）
   - 印尼文：12個單字以內

2. 完整性要求：說明必須是完整的句子，絕對不可以中途截斷
3. 標點符號：不要以逗號、頓號、分號、冒號結尾
4. 可接受的結尾：句號、驚嘆號、問號或直接以名詞/動詞結尾
5. 禁止使用：「...」、「etc.」、「等」、「之類」等任何省略表達
6. 內容準確：必須準確描述圖片實際內容
7. 相關性：必須與新聞內容相關
8. 語氣：客觀、中立、不帶情感色彩
9. 格式：必須使用以下 JSON 格式輸出，不要有任何前綴或說明

【輸出格式】：
{{
  "zh": "中文說明（15字以內）",
  "en": "English description (12 words max)",
  "ja": "日本語の説明（15字以内）",
  "id": "Deskripsi Indonesia (12 kata maksimal)"
}}

【中文範例】（完整且符合字數）：
✓ 總統參加經濟論壇
✓ 股市今日收盤上漲
✓ 新手機產品發表
✓ 民眾街頭示威遊行

【英文範例】：
✓ President attends economic forum
✓ Stock market closes higher today
✓ New smartphone product launch
✓ Citizens protest on streets

【日文範例】：
✓ 大統領が経済フォーラムに参加
✓ 株式市場が本日上昇
✓ 新スマートフォン製品発表
✓ 市民が街頭でデモ

【印尼文範例】：
✓ Presiden hadiri forum ekonomi
✓ Pasar saham naik hari ini
✓ Peluncuran produk smartphone baru
✓ Warga berdemonstrasi di jalan

【重要提醒】：
- 四種語言的說明必須表達相同的意思
- 如果原本想表達的內容會超過字數限制，請重新組織語句
- 寧可犧牲細節，也要保證句子的完整性
- 每個字都要有意義，避免冗詞贅字
- 必須輸出有效的 JSON 格式

現在請生成符合所有要求的四種語言圖片說明（只輸出 JSON，不要其他文字）：
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
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            
            # 提取生成的文字
            response_text = response.text.strip()
            
            # 嘗試解析 JSON
            try:
                # 移除可能的 markdown 代碼塊標記
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                descriptions = json.loads(response_text)
                
                # 驗證必要的鍵存在
                required_keys = ['zh', 'en', 'ja', 'id']
                for key in required_keys:
                    if key not in descriptions:
                        raise ValueError(f"缺少 {key} 語言的說明")
                
                # 清理每種語言的說明
                for lang in required_keys:
                    descriptions[lang] = descriptions[lang].strip('"\'「」『』 ')
                
                print(f"✓ 成功生成多語言說明:")
                print(f"  中文: {descriptions['zh']} ({len(descriptions['zh'])}字)")
                print(f"  英文: {descriptions['en']} ({len(descriptions['en'].split())}詞)")
                print(f"  日文: {descriptions['ja']} ({len(descriptions['ja'])}字)")
                print(f"  印尼文: {descriptions['id']} ({len(descriptions['id'].split())}詞)")
                
                return descriptions
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  警告：無法解析 JSON 格式: {e}")
                print(f"  原始回應: {response_text[:200]}...")
                print("  將使用備用方案生成說明")
                
                # 備用方案：使用原始回應作為中文說明，其他語言用簡化版本
                description = response_text.strip('"\'「」『』 ')
            
            # 如果 JSON 解析失敗，檢查中文說明長度並處理
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
            
            print(f"   ✓ 最終中文說明：{description} ({len(description)}字)")
            
            # 備用方案：生成簡化的多語言版本
            category_translations = {
                '政治': {'zh': '政治新聞', 'en': 'Political News', 'ja': '政治ニュース', 'id': 'Berita Politik'},
                '經濟': {'zh': '經濟新聞', 'en': 'Economic News', 'ja': '経済ニュース', 'id': 'Berita Ekonomi'},
                '社會': {'zh': '社會新聞', 'en': 'Social News', 'ja': '社会ニュース', 'id': 'Berita Sosial'},
                '國際': {'zh': '國際新聞', 'en': 'International News', 'ja': '国際ニュース', 'id': 'Berita Internasional'},
                '科技': {'zh': '科技新聞', 'en': 'Technology News', 'ja': '科技ニュース', 'id': 'Berita Teknologi'},
                '體育': {'zh': '體育新聞', 'en': 'Sports News', 'ja': 'スポーツニュース', 'id': 'Berita Olahraga'},
                '娛樂': {'zh': '娛樂新聞', 'en': 'Entertainment News', 'ja': 'エンタメニュース', 'id': 'Berita Hiburan'},
            }
            
            fallback = category_translations.get(category, {
                'zh': '新聞圖片',
                'en': 'News Image',
                'ja': 'ニュース画像',
                'id': 'Gambar Berita'
            })
            
            return {
                'zh': description,
                'en': fallback['en'],
                'ja': fallback['ja'],
                'id': fallback['id']
            }
            
        except Exception as e:
            print(f"❌ 生成說明時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 使用備用說明
            return {
                'zh': f"{category}相關新聞圖片" if category else "新聞相關圖片",
                'en': "News Related Image",
                'ja': "ニュース関連画像",
                'id': "Gambar Terkait Berita"
            }
    
    def update_description(self, story_id: str, descriptions: Dict[str, str]) -> bool:
        """
        更新 generated_image 表的多語言 description 欄位
        
        Args:
            story_id: 新聞故事 ID (用於定位要更新的圖片記錄)
            descriptions: 多語言說明字典 {'zh': ..., 'en': ..., 'ja': ..., 'id': ...}
            
        Returns:
            bool: 更新是否成功
        """
        if self.dry_run:
            print("🔍 [測試模式] 不會實際寫入資料庫")
            return True
            
        try:
            # 更新四個語言欄位（使用正確的欄位名稱）
            update_data = {
                "description": descriptions.get('zh', ''),              # 中文
                "description_en_lang": descriptions.get('en', ''),       # 英文
                "description_jp_lang": descriptions.get('ja', ''),       # 日文
                "description_id_lang": descriptions.get('id', '')        # 印尼文
            }
            
            self.supabase.table("generated_image").update(update_data).eq("story_id", story_id).execute()
            
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
            
            # 3. 生成多語言說明
            print("正在生成多語言圖片說明...")
            descriptions = self.generate_description_with_vision(
                image=image,
                news_content=news_long,
                category=category
            )
            
            print("✓ 生成的說明:")
            print(f"  中文: {descriptions['zh']}")
            print(f"  英文: {descriptions['en']}")
            print(f"  日文: {descriptions['ja']}")
            print(f"  印尼文: {descriptions['id']}")
            
            # 4. 更新資料庫
            print("正在更新資料庫...")
            if self.update_description(story_id, descriptions):
                print(f"✅ 成功更新 story_id={story_id} 的多語言說明")
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
  # 生成圖片說明
  python description.py
  python description.py --no-write
  python description.py --limit 10
  python description.py --no-write --limit 5 --sleep 3.0
  
  # 檢查已生成的說明
  python description.py --check
  python description.py --check --limit 20
  python description.py --check --show-valid
  
  # 修正不符合標準的說明
  python description.py --fix
  python description.py --fix --no-write
  python description.py --fix --limit 50 --fix-limit 3
  python description.py --fix --fix-limit 5
  
  # 批量更新多語言說明
  python description.py --update
  python description.py --update --no-write
  python description.py --update --limit 100 --update-limit 5
  python description.py --update --update-limit 10
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
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='檢查模式：檢查已生成的圖片說明是否符合標準'
    )
    
    parser.add_argument(
        '--show-valid',
        action='store_true',
        help='檢查模式：同時顯示符合標準的說明（預設只顯示有問題的）'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='修正模式：重新生成不符合標準的圖片說明'
    )
    
    parser.add_argument(
        '--fix-limit',
        type=int,
        default=None,
        help='修正模式：限制實際修正的數量（從不合格項目中挑選前 N 筆）'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='更新模式：批量重新生成並更新多語言說明（無論是否符合標準）'
    )
    
    parser.add_argument(
        '--update-limit',
        type=int,
        default=None,
        help='更新模式：限制實際更新的數量（從所有圖片中挑選前 N 筆）'
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
        if args.check:
            # 檢查模式
            print("模式：檢查已生成的圖片說明\n")
            generator.check_all_descriptions(
                limit=args.limit,
                show_valid=args.show_valid
            )
        elif args.fix:
            # 修正模式
            print("模式：修正不符合標準的圖片說明\n")
            generator.fix_invalid_descriptions(
                limit=args.limit,
                fix_limit=args.fix_limit,
                sleep_time=args.sleep
            )
        elif args.update:
            # 更新模式
            print("模式：批量更新多語言圖片說明\n")
            generator.update_all_descriptions(
                limit=args.limit,
                update_limit=args.update_limit,
                sleep_time=args.sleep
            )
        else:
            # 生成模式（預設）
            print("模式：生成圖片說明\n")
            generator.process_images(limit=args.limit, sleep_time=args.sleep)
    except KeyboardInterrupt:
        print("\n\n⚠ 使用者中斷執行")
    except Exception as e:
        print(f"\n\n❌ 執行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
