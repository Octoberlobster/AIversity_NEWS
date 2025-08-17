"""
完整新聞處理流水線
將資料處理和報導生成串聯執行，直接產生最終結果
"""

import os
import sys
import json
from datetime import datetime
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

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/logs/complete_pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
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

            if not processed_result:
                logger.error("❌ 新聞處理失敗，流水線終止")
                return None

            logger.info(f"✅ 新聞處理完成：{processed_result}")

            # 第二步：報導生成
            logger.info("\n" + "="*60)
            logger.info("📝 第二步：執行報導生成")
            logger.info("="*60)

            report_result = self._run_report_generation(processed_result)

            if not report_result:
                logger.error("❌ 報導生成失敗，流水線終止")
                return None

            logger.info(f"✅ 報導生成完成：{report_result}")

                      
            db_client = SupabaseClient()
            for idx in range(len(report_result)):
                single_report = report_result[idx]
                update_data = {
                    'story_id': single_report.get('story_info').get('story_id' ,''),
                    'category': single_report.get('story_info').get('category' ,''),
                    'total_articles': single_report.get('story_info').get('total_articles' ,''),
                    'news_title': single_report.get('comprehensive_report', '').get('title', ''),
                    'ultra_short': single_report.get('comprehensive_report', '').get('versions', {}).get('ultra_short', ''),
                    'short': single_report.get('comprehensive_report', '').get('versions', {}).get('short', ''),
                    'long': single_report.get('comprehensive_report', '').get('versions', {}).get('long', ''),
                    'generated_date': single_report.get('processed_at', '')
                }
                db_client.save_to_single_news(single_report.get('story_info').get('story_id' ,''), update_data)

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
