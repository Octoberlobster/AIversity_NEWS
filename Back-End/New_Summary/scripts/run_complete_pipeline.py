"""
完整新聞處理流水線
將資料處理和報導生成串聯執行，直接產生最終結果
"""

import os
import sys
import json
from datetime import datetime
from typing import List
import logging

# 確保載入 .env 檔案
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
except ImportError:
    pass

# 添加父目錄到 Python 路徑，以便引用 core 模組
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.news_processor import NewsProcessor
from core.config import NewsProcessorConfig
from core.report_generator import ReportGenerator
from core.report_config import ReportGeneratorConfig
from core.db_client import SupabaseClient
from core.difficult_keyword_extractor_final import DiffKeywordProcessor, DiffKeywordConfig

# 設置日誌 - 為不同模組設置不同的日誌檔案
def setup_logging():
    """設置多個日誌檔案的日誌系統"""
    # 確保日誌目錄存在
    os.makedirs('outputs/logs', exist_ok=True)
    
    # 設置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除現有的 handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 設置格式化器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 設置控制台輸出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 為主程式設置日誌檔案
    main_handler = logging.FileHandler('outputs/logs/complete_pipeline.log', encoding='utf-8')
    main_handler.setFormatter(formatter)
    
    # 為不同模組設置不同的日誌檔案
    module_handlers = {
        'core.db_client': 'outputs/logs/db_client.log',
        'core.news_processor': 'outputs/logs/news_processing.log',
        'core.report_generator': 'outputs/logs/report_generation.log',
        'core.difficult_keyword_extractor_final': 'outputs/logs/keyword_extraction.log',
        'scripts.run_complete_pipeline': 'outputs/logs/complete_pipeline.log'
    }
    
    # 為每個模組創建專屬的 handler
    for module_name, log_file in module_handlers.items():
        module_logger = logging.getLogger(module_name)
        
        # 防止日誌重複到父日誌器
        module_logger.propagate = False
        
        # 創建檔案 handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 添加控制台和檔案 handler
        module_logger.addHandler(console_handler)
        module_logger.addHandler(file_handler)
        module_logger.setLevel(logging.INFO)

# 初始化日誌系統
setup_logging()
logger = logging.getLogger(__name__)

class CompletePipeline:
    """完整的新聞處理流水線"""
    
    def __init__(self, api_key: str = None):
        """初始化流水線"""
        self.api_key = api_key or NewsProcessorConfig.get_gemini_api_key()
        if not self.api_key:
            raise ValueError("未設定 GEMINI_API_KEY")
        
        logger.info("🚀 初始化完整新聞處理流水線")
        
    def run_complete_pipeline(self):
        """
        執行完整流水線
        """
        
        start_time = datetime.now()
        logger.info(f"⏰ 流水線開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 第一步：新聞資料處理
            logger.info("\n" + "="*60)
            logger.info("🔄 第一步：執行新聞資料處理")
            logger.info("="*60)
            
            processed_result = self._run_news_processing()

            if processed_result is None:
                logger.error("❌ 新聞處理失敗，流水線終止")
                return None
            
            if not processed_result:  # 空列表表示沒有新資料需要處理
                logger.info("✨ 沒有新資料需要處理，流水線正常結束")
                return []

            logger.info(f"✅ 新聞處理完成，處理了 {len(processed_result)} 個 stories")

            # 第二步：報導生成
            logger.info("\n" + "="*60)
            logger.info("📝 第二步：執行報導生成")
            logger.info("="*60)

            report_result = self._run_report_generation(processed_result)

            if not report_result:
                logger.error("❌ 報導生成失敗，流水線終止")
                return None

            logger.info(f"✅ 報導生成完成，生成了 {len(report_result)} 個報告")

            # 第三步：儲存到資料庫
            logger.info("\n" + "="*60)
            logger.info("💾 第三步：儲存摘要到資料庫")
            logger.info("="*60)
                      
            db_client = SupabaseClient()
            success_count = 0
            for idx, single_report in enumerate(report_result):
                story_id = single_report.get('story_info', {}).get('story_id', '')
                
                update_data = {
                    'story_id': story_id,
                    'category': single_report.get('story_info', {}).get('category', ''),
                    'total_articles': single_report.get('story_info', {}).get('total_articles', 0),
                    'news_title': single_report.get('comprehensive_report', {}).get('title', ''),
                    'ultra_short': single_report.get('comprehensive_report', {}).get('versions', {}).get('ultra_short', ''),
                    'short': single_report.get('comprehensive_report', {}).get('versions', {}).get('short', ''),
                    'long': single_report.get('comprehensive_report', {}).get('versions', {}).get('long', ''),
                    'generated_date': single_report.get('processed_at', '')
                }
                
                if db_client.save_to_single_news(story_id, update_data):
                    success_count += 1
                    logger.info(f"✅ 儲存成功: {story_id}")
                else:
                    logger.error(f"❌ 儲存失敗: {story_id}")
            
            logger.info(f"💾 資料庫儲存完成：{success_count}/{len(report_result)} 成功")
            
            # 第四步：生成困難關鍵字
            logger.info("\n" + "="*60)
            logger.info("🔤 第四步：生成困難關鍵字")
            logger.info("="*60)
            
            # 獲取需要生成 terms 的 story_ids
            updated_story_ids = db_client.get_updated_story_ids()
            
            if updated_story_ids:
                logger.info(f"📝 需要生成 terms 的 stories: {len(updated_story_ids)} 個")
                terms_success = self._run_keyword_extraction(list(updated_story_ids))
                
                if terms_success:
                    logger.info(f"✅ 困難關鍵字生成完成: {len(updated_story_ids)} 個 stories")
                else:
                    logger.warning("⚠️ 困難關鍵字生成部分失敗，但不影響主流程")
            else:
                logger.info("✨ 沒有需要生成困難關鍵字的 stories")
            
            # 清空更新記錄
            db_client.clear_updated_story_ids()
            
            # 結束
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"\n🎉 流水線執行完成！")
            logger.info(f"⏰ 總耗時: {duration}")
            logger.info(f"📊 處理結果: {len(processed_result)} stories → {len(report_result)} reports → {success_count} saved")
            if updated_story_ids:
                logger.info(f"🔤 困難關鍵字: {len(updated_story_ids)} stories")
            
            return report_result

        except Exception as e:
            logger.error(f"❌ 流水線執行過程中發生錯誤：{e}")
            return None
    
    def _run_news_processing(self):
        """執行新聞資料處理"""
        try:
            
            # 初始化新聞處理器
            processor = NewsProcessor(
                api_key=self.api_key, 
                model_name=NewsProcessorConfig.GEMINI_MODEL
            )
            
            # 執行處理
            processor_result = processor.process_all_stories()
            return processor_result

        except Exception as e:
            logger.error(f"❌ 新聞處理失敗：{e}")
            return None
    
    def _run_report_generation(self, processed_result):
        """執行報導生成"""
        try:
            # 初始化報導生成器
            generator = ReportGenerator(
                api_key=self.api_key,
                model_name=ReportGeneratorConfig.GEMINI_MODEL
            )
            
            
            # 執行報導生成（只生成綜合報導）
            generator_result = generator.generate_reports_for_all_stories(processed_result)
            return generator_result
            
        except Exception as e:
            logger.error(f"❌ 報導生成失敗：{e}")
            return None
    
    def _run_keyword_extraction(self, updated_story_ids: List[str]) -> bool:
        """執行困難關鍵字提取"""
        try:
            logger.info(f"🔤 開始為 {len(updated_story_ids)} 個 stories 生成困難關鍵字...")
            
            # 初始化困難關鍵字提取器
            keyword_processor = DiffKeywordProcessor()
            
            if not keyword_processor.is_ready():
                logger.warning("困難關鍵字提取器未準備就緒")
                return False
            keyword_processor.run(limit=None, story_ids=updated_story_ids)
            
            logger.info("✅ 困難關鍵字提取完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 困難關鍵字提取失敗：{e}")
            return False

def main():
    """主執行函數"""
    print("🚀 完整新聞處理流水線")
    print("="*50)
    
    # 檢查 API Key
    api_key = NewsProcessorConfig.get_gemini_api_key()
    if not api_key:
        print("❌ 未設定 GEMINI_API_KEY")
        print("請在 .env 檔案中設定 GEMINI_API_KEY=your_api_key")
        return
    
    print("✅ API Key 已設定")

    
    try:
        # 創建流水線
        pipeline = CompletePipeline(api_key=api_key)
        
        # 執行完整流水線
        generator_result = pipeline.run_complete_pipeline()
        
        if generator_result:
            print("\n🎉 流水線執行成功！")
            print(f"📄 最終輸出：{generator_result}")
        else:
            print("\n❌ 流水線執行失敗")
            
    except Exception as e:
        logger.error(f"❌ 主程式執行失敗：{e}")
        print(f"\n❌ 執行失敗：{e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 使用者中斷執行")
    except Exception as e:
        print(f"\n❌ 程式執行失敗：{e}")
