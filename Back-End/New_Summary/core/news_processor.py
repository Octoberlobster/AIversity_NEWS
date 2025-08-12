import json
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from google import genai
from google.genai import types  # 新版 SDK 的型別
from core.config import NewsProcessorConfig

# 設置日誌
try:
    os.makedirs(NewsProcessorConfig.LOG_DIR, exist_ok=True)
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(NewsProcessorConfig.LOG_DIR, 'news_processing.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsProcessor:
    """新聞處理器 - 負責處理新聞數據的摘要和關鍵詞萃取（新版 google-genai）"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化新聞處理器

        Args:
            api_key: Gemini API 金鑰（可省略，將自 config 或環境變數讀取）
            model_name: 使用的 Gemini 模型名稱
        """
        # 取得 API Key（參數優先，其次 config，最後環境變數）
        self.api_key = api_key or getattr(NewsProcessorConfig, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("找不到 Gemini API 金鑰。請在參數、NewsProcessorConfig 或環境變數 GEMINI_API_KEY 設定。")

        # 建立新版 GenAI Client
        self.client = genai.Client(api_key=self.api_key)

        # 模型名稱
        self.model_name = model_name or NewsProcessorConfig.GEMINI_MODEL

        # 參數來源於 Config
        self.generation_configs = getattr(NewsProcessorConfig, "GENERATION_CONFIGS", {})  # dict，例如 {"analysis": {...}}
        self.safety_settings = getattr(NewsProcessorConfig, "SAFETY_SETTINGS", [])        # list[dict] 或 list[types.SafetySetting]

    # ===== 工具：把 config/safety 映射成新版 SDK 型別 =====
    def _to_safety_settings(self) -> List[types.SafetySetting]:
        result: List[types.SafetySetting] = []
        for s in (self.safety_settings or []):
            if isinstance(s, types.SafetySetting):
                result.append(s)
            elif isinstance(s, dict):
                # 期望 keys: category, threshold
                result.append(types.SafetySetting(
                    category=s.get("category"),
                    threshold=s.get("threshold")
                ))
        return result

    def _build_generate_config(self, preset: str = "analysis") -> types.GenerateContentConfig:
        # 從 config 取出預設的生成參數（如 temperature、top_p、max_output_tokens、stop_sequences 等）
        base: Dict[str, Any] = dict(self.generation_configs.get(preset, {}))

        # 啟用 JSON Mode，降低下游 JSON 解析困難
        base.setdefault("response_mime_type", "application/json")

        # 整合 safety settings（新版放在 config 裡）
        base["safety_settings"] = self._to_safety_settings()

        return types.GenerateContentConfig(**base)

    # ===== 業務邏輯 =====
    def create_article_summary_prompt(self, article: Dict, summary_type: str = "analysis") -> str:
        """
        創建單篇文章摘要的 prompt
        """
        max_chars = NewsProcessorConfig.MAX_CONTENT_LENGTH
        base_prompt = f"""
            你是專業的新聞編輯，請分析以下新聞文章並提取關鍵資訊。

            【新聞資料】
            標題：{article.get('article_title', '無標題')}
            發布時間：{article.get('publish_date') or article.get('crawl_date', '未知時間')}
            內容：{(article.get('content') or '無內容')[:max_chars]}

            【任務要求】
            請提取以下資訊並以 JSON 格式輸出：

            1. 核心摘要（2-3句話概括主要事件）
            2. 關鍵詞列表（5-8個最重要的關鍵詞）
            3. 重要人物（提及的重要人物姓名）
            4. 重要機構組織（提及的公司、政府部門、學術機構等）
            5. 地點資訊（涉及的地理位置）
            6. 時間線（重要的時間點）
            7. 事件分類（政治、經濟、科技、社會等）

            【輸出格式】
            請嚴格按照以下 JSON 格式輸出，不要包含其他文字：

            {{
                "core_summary": "核心摘要內容",
                "keywords": ["關鍵詞1", "關鍵詞2", "關鍵詞3"],
                "key_persons": ["人物1", "人物2"],
                "key_organizations": ["組織1", "組織2"],
                "locations": ["地點1", "地點2"],
                "timeline": ["時間點1", "時間點2"],
                "category": "事件分類",
                "confidence_score": 0.95
            }}
        """
        return base_prompt.strip()

    def process_single_article(self, article: Dict) -> Optional[Dict]:
        """
        處理單篇文章
        """
        try:
            # 檢查文章內容
            if not article.get('content') or len(article['content'].strip()) < 50:
                logger.warning(f"文章 {article.get('id', 'unknown')} 內容太短或為空")
                return None

            # 構造 prompt 與生成參數
            prompt = self.create_article_summary_prompt(article)
            gen_config = self._build_generate_config("analysis")

            # 呼叫新版 Gemini 介面
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=gen_config
            )

            # 解析回應
            if getattr(response, "text", None):
                try:
                    clean_text = response.text.strip()

                    # 移除可能的 ```json 包裝（理論上 JSON Mode 就不會有了，但保險留著）
                    if clean_text.startswith('```json'):
                        start_idx = clean_text.find('{')
                        end_idx = clean_text.rfind('}') + 1
                        if start_idx != -1 and end_idx != 0:
                            clean_text = clean_text[start_idx:end_idx]
                    elif clean_text.startswith('```'):
                        lines = clean_text.split('\n')
                        if len(lines) > 2:
                            clean_text = '\n'.join(lines[1:-1])

                    result = json.loads(clean_text)

                    # 添加原始文章資訊
                    result.update({
                        "original_article_id": article.get('id'),
                        "original_title": article.get('article_title'),
                        "publish_date": article.get('publish_date') or article.get('crawl_date'),
                        "source_url": article.get('final_url'),
                        "processed_at": datetime.now().isoformat()
                    })

                    logger.info(f"成功處理文章: {article.get('article_title', '')[:50]}...")
                    return result

                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失敗: {e}")
                    logger.error(f"清理後的文字: {clean_text[:200]}...")
                    logger.error(f"原始回應: {response.text[:200]}...")
                    return None
            else:
                logger.error("Gemini API 回應為空")
                return None

        except Exception as e:
            logger.error(f"處理文章時發生錯誤: {e}")
            return None

    def process_story_articles(self, story: Dict) -> Dict:
        """
        處理單個 story 中的所有 articles
        """
        story_id = story.get('story_index', 'unknown')
        logger.info(f"開始處理 Story {story_id}: {story.get('story_title', '')}")

        articles = story.get('articles', [])
        processed_articles = []
        failed_articles = []

        for i, article in enumerate(articles):
            logger.info(f"處理 Story {story_id} 的第 {i+1}/{len(articles)} 篇文章...")
            result = self.process_single_article(article)

            if result:
                processed_articles.append(result)
            else:
                failed_articles.append({
                    "article_id": article.get('id'),
                    "article_title": article.get('article_title'),
                    "reason": "處理失敗"
                })

            # 添加延遲避免 API 速率限制
            time.sleep(NewsProcessorConfig.API_DELAY)

        story_result = {
            "story_index": story_id,
            "story_title": story.get('story_title'),
            "category": story.get('category'),
            "total_articles": len(articles),
            "processed_articles": len(processed_articles),
            "failed_articles": len(failed_articles),
            "articles_analysis": processed_articles,
            "failed_list": failed_articles,
            "processed_at": datetime.now().isoformat()
        }

        logger.info(f"Story {story_id} 處理完成: 成功 {len(processed_articles)}/{len(articles)} 篇")
        return story_result

    def load_news_data(self, file_path: str) -> List[Dict]:
        """
        載入新聞數據檔案
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功載入 {len(data)} 個 stories")
            return data
        except Exception as e:
            logger.error(f"載入檔案失敗: {e}")
            return []

    def save_processed_data(self, data: List[Dict], output_path: str):
        """
        保存處理結果
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"處理結果已保存至: {output_path}")
        except Exception as e:
            logger.error(f"保存檔案失敗: {e}")

    def process_all_stories(self, input_file: str, output_file: str, start_index: int = 0, max_stories: Optional[int] = None):
        """
        處理所有 stories
        """
        logger.info("=== 開始新聞處理流程 ===")

        input_file = input_file or NewsProcessorConfig.INPUT_FILE
        stories = self.load_news_data(input_file)
        if not stories:
            logger.error("無法載入新聞數據")
            return

        end_index = len(stories)
        if max_stories:
            end_index = min(start_index + max_stories, len(stories))

        logger.info(f"將處理 stories {start_index} 到 {end_index-1} (共 {end_index-start_index} 個)")

        processed_stories = []

        for i in range(start_index, end_index):
            story = stories[i]
            try:
                logger.info(f"\n=== 處理進度: {i+1-start_index}/{end_index-start_index} ===")
                result = self.process_story_articles(story)
                processed_stories.append(result)

                # 定期保存進度
                if (i - start_index + 1) % 5 == 0:
                    temp_output = output_file.replace('.json', f'_progress_{i+1}.json')
                    self.save_processed_data(processed_stories, temp_output)
                    logger.info(f"進度已保存: {temp_output}")

            except Exception as e:
                logger.error(f"處理 Story {i} 時發生嚴重錯誤: {e}")
                continue

        output_file = output_file or NewsProcessorConfig.get_output_filename(prefix="processed_articles")
        self.save_processed_data(processed_stories, output_file)
        self.generate_processing_report(processed_stories, output_file.replace('.json', '_report.txt'))
        logger.info("=== 新聞處理流程完成 ===")

    def generate_processing_report(self, processed_data: List[Dict], report_path: str):
        """
        生成處理報告
        """
        total_stories = len(processed_data)
        total_articles = sum(story.get('total_articles', 0) for story in processed_data)
        successful_articles = sum(story.get('processed_articles', 0) for story in processed_data)

        report = f"""
新聞處理報告
====================
處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

統計資訊:
- 處理 Stories 總數: {total_stories}
- 文章總數: {total_articles}
- 成功處理文章數: {successful_articles}
- 成功率: {successful_articles/total_articles*100:.1f}%

各 Story 處理詳情:
"""

        for story in processed_data:
            report += f"\nStory {story.get('story_index')}: {story.get('story_title')}"
            report += f"\n  - 文章數: {story.get('total_articles')}"
            report += f"\n  - 成功: {story.get('processed_articles')}"
            report += f"\n  - 失敗: {story.get('failed_articles')}"

        try:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"處理報告已生成: {report_path}")
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")

def main():
    """主函數 - 簡易測試，讀取 Config"""
    api_key = NewsProcessorConfig.get_gemini_api_key()
    processor = NewsProcessor(api_key=api_key, model_name=NewsProcessorConfig.GEMINI_MODEL)
    processor.process_all_stories(
        input_file=NewsProcessorConfig.INPUT_FILE,
        output_file=NewsProcessorConfig.get_output_filename(prefix="processed_articles"),
        start_index=0,
        max_stories=2
    )

if __name__ == "__main__":
    main()