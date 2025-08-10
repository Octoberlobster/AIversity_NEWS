
"""
報導生成器 - 基於處理後的新聞資料生成各種類型的報導
功能：
1. 單篇文章的長/中/短摘要生成
2. 多篇文章的綜合報導生成
3. 關鍵詞和人物/機構的整合
"""

import json
import google.generativeai as genai
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os
from collections import Counter, defaultdict
from core.report_config import ReportGeneratorConfig

# 設置日誌
try:
    os.makedirs(ReportGeneratorConfig.LOG_DIR, exist_ok=True)
except Exception:
    pass
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(ReportGeneratorConfig.LOG_DIR, 'report_generation.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ReportGenerator:
    """報導生成器 - 負責生成各種類型的新聞報導"""
    
    def __init__(self, api_key: str, model_name: Optional[str] = None):
        """
        初始化報導生成器
        
        Args:
            api_key: Gemini API 金鑰
            model_name: 使用的 Gemini 模型名稱
        """
        # 配置 Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name or ReportGeneratorConfig.GEMINI_MODEL)
        # 從 Config 取得參數
        self.generation_configs = ReportGeneratorConfig.GENERATION_CONFIGS
        self.api_delay = ReportGeneratorConfig.API_DELAY
        
    def create_single_article_prompt(self, article_data: Dict, summary_type: str) -> str:
        """為單篇文章生成不同類型摘要的 prompt"""
        
        base_info = f"""
文章標題：{article_data.get('original_title', '')}
發布時間：{article_data.get('publish_date', '')}
分類：{article_data.get('category', '')}
核心摘要：{article_data.get('core_summary', '')}
關鍵詞：{', '.join(article_data.get('keywords', []))}
重要人物：{', '.join(article_data.get('key_persons', []))}
相關機構：{', '.join(article_data.get('key_organizations', []))}
地點：{', '.join(article_data.get('locations', []))}
時間軸：{', '.join(article_data.get('timeline', []))}
"""

        if summary_type == "short":
            prompt = f"""
基於以下文章資訊，生成一個簡潔的短摘要，適合用於新聞列表預覽：

{base_info}

要求：
1. 長度：50-80字
2. 突出最核心的新聞要點
3. 適合在點擊前讓讀者快速了解內容
4. 語言流暢自然
5. 包含最重要的關鍵詞

請直接輸出摘要內容，不需要其他解釋。
"""
        
        elif summary_type == "medium":
            prompt = f"""
基於以下文章資訊，生成一個中等長度的摘要，適合快速閱讀：

{base_info}

要求：
1. 長度：150-250字
2. 包含主要事實和背景資訊
3. 涵蓋重要人物、機構、時間點
4. 提及關鍵數據或影響
5. 結構清晰，分段明確
6. 語言專業但易懂

請直接輸出摘要內容，不需要其他解釋。
"""
        
        elif summary_type == "long":
            prompt = f"""
基於以下文章資訊，生成一個詳細的長摘要，適合深度閱讀：

{base_info}

要求：
1. 長度：400-600字
2. 完整描述事件的來龍去脈
3. 詳細介紹相關人物和機構
4. 提供充分的背景資訊和分析
5. 包含具體數據、時間、地點
6. 分析可能的影響和意義
7. 結構完整，邏輯清晰
8. 專業的新聞寫作風格

請直接輸出摘要內容，不需要其他解釋。
"""
        
        return prompt
    
    def create_comprehensive_report_prompt(self, story_data: Dict, articles_data: List[Dict], version: str = "long") -> str:
        """為多篇文章生成綜合報導的 prompt

        version: "ultra_short" | "short" | "long"
        """
        
        # 整合所有關鍵資訊
        all_keywords = []
        all_persons = []
        all_organizations = []
        all_locations = []
        all_timeline = []
        core_summaries = []
        
        for article in articles_data:
            all_keywords.extend(article.get('keywords', []))
            all_persons.extend(article.get('key_persons', []))
            all_organizations.extend(article.get('key_organizations', []))
            all_locations.extend(article.get('locations', []))
            all_timeline.extend(article.get('timeline', []))
            core_summaries.append(article.get('core_summary', ''))
        
        # 統計頻次並去重
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, v in keyword_counts.most_common(10)]
        
        person_counts = Counter(all_persons)
        top_persons = [k for k, v in person_counts.most_common(5)]
        
        org_counts = Counter(all_organizations)
        top_organizations = [k for k, v in org_counts.most_common(5)]
        
        unique_locations = list(set(all_locations))
        unique_timeline = sorted(list(set(all_timeline)))
        
        length_cfg = ReportGeneratorConfig.COMPREHENSIVE_LENGTHS.get(version, ReportGeneratorConfig.COMPREHENSIVE_LENGTHS["long"])
        min_chars = length_cfg["min_chars"]
        max_chars = length_cfg["max_chars"]

        prompt = f"""
基於以下多篇相關文章的資訊，生成一篇綜合報導：

專題：{story_data.get('story_title', '')}
分類：{story_data.get('category', '')}
文章數量：{len(articles_data)}篇

核心內容摘要：
{chr(10).join([f"• {summary}" for summary in core_summaries[:5]])}

主要關鍵詞：{', '.join(top_keywords)}
重要人物：{', '.join(top_persons)}
相關機構：{', '.join(top_organizations)}
涉及地點：{', '.join(unique_locations)}
時間軸：{', '.join(unique_timeline)}

要求：
1. 長度：{min_chars}-{max_chars}字
2. 整合所有文章的核心資訊，去除重複內容
3. 按邏輯順序組織內容（背景→發展→現狀→影響）
4. 突出最重要的人物、機構、數據
5. 提供完整的時間脈絡
6. 分析事件的意義和可能影響
7. 使用專業的新聞報導寫作風格
8. 結構清晰，使用適當的段落分隔
9. 確保資訊準確，避免推測

請生成一篇完整的綜合報導，包含標題和正文。
"""
        
        return prompt
    
    def generate_single_article_summaries(self, article_data: Dict) -> Dict[str, str]:
        """為單篇文章生成長中短三種摘要"""
        
        summaries = {}
        
        for summary_type in ["short", "medium", "long"]:
            try:
                logger.info(f"生成 {summary_type} 摘要 - 文章：{article_data.get('original_title', 'Unknown')[:50]}...")
                
                prompt = self.create_single_article_prompt(article_data, summary_type)
                config = self.generation_configs[f"{summary_type}_summary"]
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=config
                )
                
                if response.text:
                    summaries[f"{summary_type}_summary"] = response.text.strip()
                    logger.info(f"✅ {summary_type} 摘要生成成功")
                else:
                    logger.warning(f"⚠️ {summary_type} 摘要生成失敗：空回應")
                    summaries[f"{summary_type}_summary"] = ""
                
                # API 調用延遲
                time.sleep(self.api_delay)
                
            except Exception as e:
                logger.error(f"❌ {summary_type} 摘要生成失敗：{e}")
                summaries[f"{summary_type}_summary"] = ""
        
        return summaries
    
    def generate_comprehensive_report(self, story_data: Dict, articles_data: List[Dict]) -> Dict[str, Any]:
        """生成綜合報導（同時輸出三種長度版本）"""
        
        try:
            logger.info(f"生成綜合報導 - 專題：{story_data.get('story_title', 'Unknown')}")
            
            outputs = {}
            for version, cfg_key in (
                ("ultra_short", "comprehensive_ultra_short"),
                ("short", "comprehensive_short"),
                ("long", "comprehensive_long"),
            ):
                prompt = self.create_comprehensive_report_prompt(story_data, articles_data, version=version)
                config = self.generation_configs[cfg_key]
                response = self.model.generate_content(
                    prompt,
                    generation_config=config
                )
                if response.text:
                    content = response.text.strip()
                    lines = content.split('\n')
                    title = lines[0].strip()
                    body = '\n'.join(lines[1:]).strip()
                    if len(title) > 100 or not title:
                        title = f"{story_data.get('category', '')}專題報導：{story_data.get('story_title', '')}"
                        body = content
                    outputs[version] = {
                        "content": body,
                        "generated_at": datetime.now().isoformat(timespec='minutes')
                    }
                else:
                    outputs[version] = {
                        "title": "",
                        "content": ""
                    }
                time.sleep(self.api_delay)

            # 長版作為主標題（向後相容）
            main = outputs.get("long", {})
            result = {
                "title": main.get("title", ""),
                "content": main.get("content", ""),
                "versions": outputs,  # 新增：三種版本都存這裡
                "article_count": len(articles_data),
                "generated_at": datetime.now().isoformat(timespec='minutes')
            }
            logger.info("✅ 綜合報導（多版本）生成成功")
            return result
                
        except Exception as e:
            logger.error(f"❌ 綜合報導生成失敗：{e}")
            return {}
    
    def process_story_reports(self, story_data: Dict, generate_individual: bool = False) -> Dict[str, Any]:
        """處理單個 story 的所有報導生成"""
        
        articles_data = story_data.get('articles_analysis', [])
        if not articles_data:
            logger.warning(f"Story {story_data.get('story_index')} 沒有可處理的文章資料")
            return {}
        
        logger.info(f"開始處理 Story {story_data.get('story_index')} - {len(articles_data)} 篇文章")
        
        result = {
            "story_info": {
                "story_index": story_data.get('story_index'),
                "story_title": story_data.get('story_title'),
                "category": story_data.get('category'),
                "total_articles": len(articles_data)
            },
            "comprehensive_report": {},
            "processing_stats": {
                "processed_articles": len(articles_data),
                "successful_summaries": 0,
                "failed_summaries": 0
            }
        }
        
        # 只生成個別摘要（如果需要）
        if generate_individual:
            result["individual_summaries"] = []
            for i, article_data in enumerate(articles_data):
                logger.info(f"處理文章 {i+1}/{len(articles_data)}")
                
                summaries = self.generate_single_article_summaries(article_data)
                
                article_result = {
                    "article_id": article_data.get('original_article_id'),
                    "original_title": article_data.get('original_title'),
                    "publish_date": article_data.get('publish_date'),
                    "source_url": article_data.get('source_url'),
                    "summaries": summaries,
                    "original_analysis": {
                        "keywords": article_data.get('keywords', []),
                        "key_persons": article_data.get('key_persons', []),
                        "key_organizations": article_data.get('key_organizations', []),
                        "confidence_score": article_data.get('confidence_score', 0)
                    }
                }
                
                result["individual_summaries"].append(article_result)
                
                # 統計成功生成的摘要數量
                successful_summaries = sum(1 for k, v in summaries.items() if v.strip())
                result["processing_stats"]["successful_summaries"] += successful_summaries
                result["processing_stats"]["failed_summaries"] += (3 - successful_summaries)
        
        # 生成綜合報導（主要功能）
        logger.info("生成綜合報導...")
        comprehensive_report = self.generate_comprehensive_report(story_data, articles_data)
        result["comprehensive_report"] = comprehensive_report
        
        # 如果綜合報導生成成功，更新統計
        if comprehensive_report.get('title'):
            result["processing_stats"]["comprehensive_report_success"] = True
        else:
            result["processing_stats"]["comprehensive_report_success"] = False
        
        result["processed_at"] = datetime.now().isoformat()
        
        logger.info(f"Story {story_data.get('story_index')} 處理完成")
        return result
    
    def load_processed_data(self, file_path: str) -> List[Dict]:
        """載入已處理的新聞資料"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功載入資料：{len(data)} 個 stories")
            return data
        except Exception as e:
            logger.error(f"載入資料失敗：{e}")
            return []
    
    def save_reports(self, reports_data: List[Dict], output_path: str):
        """保存生成的報導"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(reports_data, f, ensure_ascii=False, indent=2)
            logger.info(f"報導已保存至：{output_path}")
        except Exception as e:
            logger.error(f"保存報導失敗：{e}")
    
    def generate_reports_for_all_stories(self, input_file: Optional[str], output_file: str, 
                                       start_index: int = 0, max_stories: Optional[int] = None,
                                       generate_individual: bool = False):
        """為所有 stories 生成報導"""
        
        # 載入資料
        # 若未指定，從設定中尋找最新的處理檔案
        input_file = input_file or ReportGeneratorConfig.find_latest_processed_file()
        stories_data = self.load_processed_data(input_file)
        if not stories_data:
            logger.error("沒有可處理的資料")
            return
        
        # 確定處理範圍
        end_index = len(stories_data)
        if max_stories:
            end_index = min(start_index + max_stories, len(stories_data))
        
        stories_to_process = stories_data[start_index:end_index]
        
        if generate_individual:
            logger.info(f"準備處理 {len(stories_to_process)} 個 stories (包含個別摘要和綜合報導)")
        else:
            logger.info(f"準備處理 {len(stories_to_process)} 個 stories (僅生成綜合報導)")
        
        logger.info(f"處理範圍: 索引 {start_index}-{end_index-1}")
        
        results = []
        
        for i, story_data in enumerate(stories_to_process):
            actual_index = start_index + i
            logger.info(f"\n{'='*60}")
            logger.info(f"處理 Story {actual_index + 1}/{len(stories_data)}")
            logger.info(f"{'='*60}")
            
            try:
                story_reports = self.process_story_reports(story_data, generate_individual=generate_individual)
                if story_reports:
                    results.append(story_reports)
                    logger.info(f"✅ Story {actual_index + 1} 處理成功")
                else:
                    logger.warning(f"⚠️ Story {actual_index + 1} 處理失敗")
                
            except Exception as e:
                logger.error(f"❌ Story {actual_index + 1} 處理過程中發生錯誤：{e}")
                continue
        
        # 保存結果
        if results:
            # 若未提供輸出路徑，使用設定檔命名
            if not output_file:
                output_file = ReportGeneratorConfig.get_output_filename(prefix="final_comprehensive_reports")
            self.save_reports(results, output_file)
            self.generate_reports_summary(results, output_file.replace('.json', '_summary.txt'))
        
        logger.info(f"\n🎉 報導生成完成！成功處理 {len(results)} 個 stories")
    
    def generate_reports_summary(self, reports_data: List[Dict], summary_path: str):
        """生成報導處理摘要"""
        
        total_stories = len(reports_data)
        total_articles = sum(r.get('story_info', {}).get('total_articles', 0) for r in reports_data)
        total_individual_summaries = sum(r.get('processing_stats', {}).get('successful_summaries', 0) for r in reports_data)
        total_comprehensive = sum(1 for r in reports_data if r.get('comprehensive_report', {}).get('title'))
        
        # 檢查是否包含個別摘要
        has_individual = any('individual_summaries' in r for r in reports_data)
        
        summary_content = f"""
報導生成摘要
====================
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
生成模式: {'綜合報導 + 個別摘要' if has_individual else '僅綜合報導'}

統計資訊:
- 處理 Stories 總數: {total_stories}
- 文章總數: {total_articles}
- 生成綜合報導數: {total_comprehensive}"""

        if has_individual:
            summary_content += f"""
- 生成個別摘要總數: {total_individual_summaries}"""
        
        summary_content += """

各 Story 詳情:
"""
        
        for report in reports_data:
            story_info = report.get('story_info', {})
            stats = report.get('processing_stats', {})
            comprehensive = report.get('comprehensive_report', {})
            
            summary_content += f"""
Story {story_info.get('story_index', 'Unknown')}: {story_info.get('story_title', 'Unknown')}
  - 分類: {story_info.get('category', 'Unknown')}
  - 文章數: {story_info.get('total_articles', 0)}
  - 綜合報導: {'✅' if comprehensive.get('title') else '❌'}"""
            
            if comprehensive.get('title'):
                content_length = len(comprehensive.get('content', ''))
                summary_content += f"""
  - 報導長度: {content_length} 字"""
            
            if has_individual:
                summary_content += f"""
  - 個別摘要: {stats.get('successful_summaries', 0)} 成功 / {stats.get('failed_summaries', 0)} 失敗"""
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            logger.info(f"摘要報告已保存至：{summary_path}")
        except Exception as e:
            logger.error(f"保存摘要報告失敗：{e}")
