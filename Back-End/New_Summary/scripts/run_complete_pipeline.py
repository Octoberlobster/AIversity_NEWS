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

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_pipeline.log', encoding='utf-8'),
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
        
    def run_complete_pipeline(self, 
                            input_file: str = "cleaned_final_news.json",
                            output_prefix: str = "final_reports",
                            process_all: bool = True,
                            start_index: int = 0,
                            max_stories: int = None):
        """
        執行完整流水線
        
        Args:
            input_file: 原始新聞檔案
            output_prefix: 輸出檔案前綴
            process_all: 是否處理所有 stories
            start_index: 開始索引
            max_stories: 最大處理數量
        """
        
        start_time = datetime.now()
        logger.info(f"⏰ 流水線開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 第一步：新聞資料處理
            logger.info("\n" + "="*60)
            logger.info("🔄 第一步：執行新聞資料處理")
            logger.info("="*60)
            
            processed_file = self._run_news_processing(
                input_file=input_file,
                start_index=start_index,
                max_stories=max_stories
            )
            
            if not processed_file:
                logger.error("❌ 新聞處理失敗，流水線終止")
                return None
            
            logger.info(f"✅ 新聞處理完成：{processed_file}")
            
            # 第二步：報導生成
            logger.info("\n" + "="*60)
            logger.info("📝 第二步：執行報導生成")
            logger.info("="*60)
            
            final_reports_file = self._run_report_generation(
                processed_file=processed_file,
                output_prefix=output_prefix
            )
            
            if not final_reports_file:
                logger.error("❌ 報導生成失敗，流水線終止")
                return None
            
            logger.info(f"✅ 報導生成完成：{final_reports_file}")
            
            # 第三步：生成最終摘要
            self._generate_final_summary(processed_file, final_reports_file, start_time)
            
            return final_reports_file
            
        except Exception as e:
            logger.error(f"❌ 流水線執行過程中發生錯誤：{e}")
            return None
    
    def _run_news_processing(self, input_file: str, start_index: int, max_stories: int):
        """執行新聞資料處理"""
        try:
            # 檢查輸入檔案
            if not os.path.exists(input_file):
                logger.error(f"❌ 輸入檔案不存在：{input_file}")
                return None
            
            # 初始化新聞處理器
            processor = NewsProcessor(
                api_key=self.api_key, 
                model_name=NewsProcessorConfig.GEMINI_MODEL
            )
            
            # 生成輸出檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"../outputs/processed/processed_articles_{timestamp}.json"
            
            # 執行處理
            processor.process_all_stories(
                input_file=input_file,
                output_file=output_file,
                start_index=start_index,
                max_stories=max_stories
            )
            
            # 檢查輸出檔案是否生成
            if os.path.exists(output_file):
                return output_file
            else:
                logger.error("❌ 新聞處理輸出檔案未生成")
                return None
                
        except Exception as e:
            logger.error(f"❌ 新聞處理失敗：{e}")
            return None
    
    def _run_report_generation(self, processed_file: str, output_prefix: str):
        """執行報導生成"""
        try:
            # 初始化報導生成器
            generator = ReportGenerator(
                api_key=self.api_key,
                model_name=ReportGeneratorConfig.GEMINI_MODEL
            )
            
            # 生成輸出檔名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"../outputs/reports/{output_prefix}_{timestamp}.json"
            
            # 執行報導生成（只生成綜合報導）
            generator.generate_reports_for_all_stories(
                input_file=processed_file,
                output_file=output_file,
                generate_individual=False  # 只生成綜合報導
            )
            
            # 檢查輸出檔案是否生成
            if os.path.exists(output_file):
                return output_file
            else:
                logger.error("❌ 報導生成輸出檔案未生成")
                return None
                
        except Exception as e:
            logger.error(f"❌ 報導生成失敗：{e}")
            return None
    
    def _generate_final_summary(self, processed_file: str, reports_file: str, start_time: datetime):
        """生成最終摘要報告"""
        try:
            end_time = datetime.now()
            duration = end_time - start_time
            
            # 讀取統計資訊
            processed_stats = self._get_file_stats(processed_file)
            reports_stats = self._get_file_stats(reports_file)
            
            summary_content = f"""
完整新聞處理流水線執行報告
===============================
執行時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%Y-%m-%d %H:%M:%S')}
總耗時: {duration}

檔案資訊:
- 原始檔案: cleaned_final_news.json
- 處理結果: {os.path.basename(processed_file)}
- 最終報導: {os.path.basename(reports_file)}

處理統計:
{processed_stats}

報導統計:
{reports_stats}

🎉 流水線執行完成！
最終輸出檔案: {reports_file}
"""
            
            # 保存摘要報告
            summary_file = reports_file.replace('.json', '_pipeline_summary.txt')
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            logger.info(f"📊 最終摘要報告已保存：{summary_file}")
            logger.info("\n" + "="*60)
            logger.info("🎉 完整流水線執行完成！")
            logger.info(f"⏰ 總耗時：{duration}")
            logger.info(f"📄 最終輸出：{reports_file}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ 生成最終摘要失敗：{e}")
    
    def _get_file_stats(self, file_path: str):
        """獲取檔案統計資訊"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'story_info' in data[0]:  # 報導檔案
                total_stories = len(data)
                total_articles = sum(item.get('story_info', {}).get('total_articles', 0) for item in data)
                successful_reports = sum(1 for item in data if item.get('comprehensive_report', {}).get('title'))
                
                return f"""- Stories 總數: {total_stories}
- 文章總數: {total_articles}
- 成功生成綜合報導: {successful_reports}"""
            
            else:  # 處理檔案
                total_stories = len(data)
                total_articles = sum(item.get('total_articles', 0) for item in data)
                successful_articles = sum(item.get('processed_articles', 0) for item in data)
                
                return f"""- Stories 總數: {total_stories}
- 文章總數: {total_articles}
- 成功處理文章: {successful_articles}"""
                
        except Exception as e:
            return f"讀取統計資訊失敗：{e}"


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
    
    # 檢查輸入檔案
    input_file = "cleaned_final_news.json"
    if not os.path.exists(input_file):
        print(f"❌ 輸入檔案不存在：{input_file}")
        return
    
    print(f"✅ 輸入檔案存在：{input_file}")
    
    # 確保輸出目錄存在
    os.makedirs("processed", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    try:
        # 創建流水線
        pipeline = CompletePipeline(api_key=api_key)
        
        # 執行完整流水線
        final_output = pipeline.run_complete_pipeline(
            input_file=input_file,
            output_prefix="comprehensive_reports"
        )
        
        if final_output:
            print("\n🎉 流水線執行成功！")
            print(f"📄 最終輸出檔案：{final_output}")
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
