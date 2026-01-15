import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os
from collections import Counter
from pydantic import BaseModel
from google import genai
from google.genai import types  # 新版 SDK 型別
from core.report_config import ReportGeneratorConfig
from core.db_client import SupabaseClient

logger = logging.getLogger(__name__)

class HintPromptResponse(BaseModel):
    title: str
    content: str

class ReportGenerator:
    """報導生成器 - 負責生成各種類型的新聞報導（新版 google-genai）"""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化報導生成器

        Args:
            api_key: Gemini API 金鑰（可省略，將自 config 或環境變數讀取）
            model_name: 使用的 Gemini 模型名稱
        """
        # 取得 API Key（參數優先，其次 config，最後環境變數）
        self.api_key = api_key or getattr(ReportGeneratorConfig, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("找不到 Gemini API 金鑰。請在參數、ReportGeneratorConfig 或環境變數 GEMINI_API_KEY 設定。")

        # 建立新版 GenAI Client
        self.client = genai.Client(api_key=self.api_key)

        # 模型名稱
        self.model_name = model_name or ReportGeneratorConfig.GEMINI_MODEL

        # 從 Config 取得生成參數/安全設定/延遲
        self.generation_configs: Dict[str, Dict[str, Any]] = getattr(ReportGeneratorConfig, "GENERATION_CONFIGS", {})
        self.safety_settings = getattr(ReportGeneratorConfig, "SAFETY_SETTINGS", [])
        self.api_delay = getattr(ReportGeneratorConfig, "API_DELAY", 0.8)

    # ===== 工具：把 safety 設定轉成新版型別，與建立 GenerateContentConfig =====
    def _to_safety_settings(self) -> List[types.SafetySetting]:
        out: List[types.SafetySetting] = []
        for s in (self.safety_settings or []):
            if isinstance(s, types.SafetySetting):
                out.append(s)
            elif isinstance(s, dict):
                out.append(types.SafetySetting(
                    category=s.get("category"),
                    threshold=s.get("threshold"),
                ))
        return out

    def _build_generate_config_by_key(self, key: str) -> types.GenerateContentConfig:
        """
        從 GENERATION_CONFIGS[key] 建立 GenerateContentConfig。
        若 force_json=True，會設置 response_mime_type 為 application/json 並指定合法的 response_schema。
        """
        base = dict(self.generation_configs.get(key, {}))
        base["response_mime_type"] = "application/json"
        base['response_schema'] = HintPromptResponse
        base["safety_settings"] = self._to_safety_settings()
        return types.GenerateContentConfig(**base)
    def create_comprehensive_report_prompt(self, story_data: Dict, articles_data: List[Dict], version: str = "long") -> str:
        """為多篇文章生成綜合報導的 prompt（version: "ultra_short" | "short" | "long"）"""

        # 整合所有關鍵資訊
        all_keywords: List[str] = []
        all_persons: List[str] = []
        all_organizations: List[str] = []
        all_locations: List[str] = []
        all_sourceurl: List[str] = []
        all_timeline: List[str] = []
        core_summaries: List[str] = []

        for article in articles_data:
            all_keywords.extend(article.get('keywords', []))
            all_persons.extend(article.get('key_persons', []))
            all_organizations.extend(article.get('key_organizations', []))
            all_locations.extend(article.get('locations', []))
            all_timeline.extend(article.get('timeline', []))
            src = article.get('article_url')
            if src:
                all_sourceurl.append(src)
            core_summaries.append(article.get('core_summary', ''))

        # 統計頻次並去重
        keyword_counts = Counter(all_keywords)
        top_keywords = [k for k, _ in keyword_counts.most_common(10)]

        person_counts = Counter(all_persons)
        top_persons = [k for k, _ in person_counts.most_common(5)]

        org_counts = Counter(all_organizations)
        top_organizations = [k for k, _ in org_counts.most_common(5)]

        unique_locations = list(dict.fromkeys(all_locations))  # 去重保序
        unique_timeline = sorted(set(all_timeline))            # 時間點字串排序

        length_cfg = ReportGeneratorConfig.COMPREHENSIVE_LENGTHS.get(
            version, ReportGeneratorConfig.COMPREHENSIVE_LENGTHS["long"]
        )
        min_chars = length_cfg["min_chars"]
        max_chars = length_cfg["max_chars"]

        # 顯示最多 10 個來源連結（若需要）
        src_preview = "\n".join([f"- {u}" for u in all_sourceurl[:10]]) if all_sourceurl else "（來源彙整）"

        schema = {
                "title": "新聞標題（20字內）",
                "content": f"新聞內文（{max_chars}字內）"
            }

        # 確保 max_chars 是 int 並且 f-string 已經被正確評估
        schema["content"] = f"新聞內文（{max_chars}字內）"
        
        prompt = f"""
            基於以下多篇相關文章的資訊，生成一篇綜合報導：

            分類：{story_data.get('category', '')}
            文章數量：{len(articles_data)} 篇

            核心內容摘要（節錄）：
            {chr(30).join([f"• {s}" for s in core_summaries[:15] if s])}

            主要關鍵詞：{', '.join(top_keywords) if top_keywords else '（無）'}
            重要人物：{', '.join(top_persons) if top_persons else '（無）'}
            相關機構：{', '.join(top_organizations) if top_organizations else '（無）'}
            涉及地點：{', '.join(unique_locations) if unique_locations else '（無）'}
            時間軸：{', '.join(unique_timeline) if unique_timeline else '（無）'}

            參考來源（節錄）：
            {src_preview}

            要求：
            1. 生成一個20字以內的新聞標題
            2. 根據版本要求生成對應長度的內文：
               - 當前版本：{version}
               - 當前字數限制：{min_chars}-{max_chars} 字
            3. 整合核心資訊，突出重要人物/機構/數據，去除重複內容
            4. 使用專業新聞寫作風格
            5. 確保資訊準確，避免推測
            6. 提供完整的時間脈絡
            7. 分析事件的影響和意義
            8. 確保資訊準確，避免推測
            9. 按邏輯順序組織內容，確保結構清晰

            請輸出一個JSON物件，包含標題和內文：
            <JSONSchema>{json.dumps(schema)}</JSONSchema>
        """.strip()

        return prompt
    def generate_comprehensive_report(self, story_data: Dict, articles_data: List[Dict]) -> Dict[str, Any]:
        """生成綜合報導（同時輸出三種長度版本）"""
        try:
            logger.info(f"生成綜合報導 - 專題：{story_data.get('story_id', 'Unknown')}")

            outputs: Dict[str, Dict[str, Any]] = {}
            main_title = ""
            for version, cfg_key in (
                ("ultra_short", "comprehensive_ultra_short"),
                ("short", "comprehensive_short"),
                ("long", "comprehensive_long"),
            ):
                prompt = self.create_comprehensive_report_prompt(story_data, articles_data, version=version)
                gen_cfg = self._build_generate_config_by_key(cfg_key)

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=gen_cfg
                )

                if response.parsed is not None:
                    # 可能是單一 BaseModel，也可能是 list[BaseModel]
                    parsed = response.parsed
                    items = parsed if isinstance(parsed, list) else [parsed]
                    for item in items:
                        # Pydantic 物件：直接用屬性
                        title = item.title
                        body  = item.content
                        outputs[version] = body
                        if version == "long":
                            main_title = title
                else:
                    # 備案：走文字或 dict
                    raw_text = (response.text or "").strip()   # 可能為 None
                    # 移除可能的 markdown 代碼塊格式
                    if raw_text.startswith("```json") and raw_text.endswith("```"):
                        raw_text = raw_text[7:-3].strip()
                    elif raw_text.startswith("```") and raw_text.endswith("```"):
                        # 處理沒有 json 標記的情況
                        raw_text = raw_text[3:-3].strip()
                    if raw_text:
                        try:
                            data = json.loads(raw_text)
                        except json.JSONDecodeError:
                            data = {}
                        title = (data.get("title") or "").strip()
                        body  = (data.get("content") or raw_text).strip()
                        outputs[version] = body
                    else:
                        outputs[version] = ""

                time.sleep(self.api_delay)
                

            # 取得所有來源 URL
            all_sourceurl = list(set(article.get('article_url') for article in articles_data if article.get('article_url')))
            result = {
                "title": main_title,
                "versions": outputs,  # 只包含各版本的 content
                "article_urls": all_sourceurl
            }
            logger.info("✅ 綜合報導（多版本）生成成功")
            return result

        except Exception as e:
            logger.error(f"❌ 綜合報導生成失敗：{e}")
            return {}

    def generate_reports_for_all_stories(self, stories_data: List[Dict[str, Any]], start_index: int = 0, max_stories: Optional[int] = None):
        """為所有 stories 生成報導"""

        if not stories_data:
            logger.error("沒有可處理的資料")
            return

        # 確定處理範圍
        end_index = len(stories_data)
        
        if max_stories:
            end_index = min(start_index + max_stories, len(stories_data))

        stories_to_process = stories_data[start_index:end_index]
        
        logger.info(f"準備處理 {len(stories_to_process)} 個 stories（包含個別摘要與綜合報導）")
        logger.info(f"處理範圍: 索引 {start_index}-{end_index-1}")

        results: List[Dict[str, Any]] = []

        for i, story_data in enumerate(stories_to_process):
            actual_index = start_index + i
            logger.info("\n" + "=" * 60)
            logger.info(f"處理 Story {actual_index + 1}/{len(stories_data)}")
            logger.info("=" * 60)

            try:
                story_reports = self.process_story_reports(story_data)
                if story_reports:
                    results.append(story_reports)
                    logger.info(f"✅ Story {actual_index + 1} 處理成功")
                else:
                    logger.warning(f"⚠️ Story {actual_index + 1} 處理失敗")

            except Exception as e:
                logger.error(f"❌ Story {actual_index + 1} 處理過程中發生錯誤：{e}")
                continue
        logger.info(f"\n🎉 報導生成完成！成功處理 {len(results)} 個 stories")
        return results

    def process_story_reports(self, story_data: Dict) -> Dict[str, Any]:
        """處理綜合報導生成"""
        articles_data = story_data.get('articles_analysis', [])
        if not articles_data:
            logger.warning(f"Story {story_data.get('story_id')} 沒有可處理的文章資料")
            return {}

        logger.info(f"開始處理 Story {story_data.get('story_id')} - {len(articles_data)} 篇文章")

        result: Dict[str, Any] = {
            "story_info": {
                "story_id": story_data.get('story_id', 'unknown'),
                "category": story_data.get('category', '未分類'),
                "total_articles": len(articles_data)
            },
            "comprehensive_report": {},
            "processing_stats": {
                "processed_articles": len(articles_data)
            }
        }

        # 僅生成綜合報導（主要功能）
        logger.info("生成綜合報導")
        comprehensive_report = self.generate_comprehensive_report(story_data, articles_data)
        result["comprehensive_report"] = comprehensive_report

        title_ok = bool((comprehensive_report.get('title') or "").strip())
        content_ok = bool((comprehensive_report.get('content') or "").strip())
        result["processing_stats"]["comprehensive_report_success"] = (title_ok or content_ok)

        result["processed_at"] = str(datetime.now().isoformat(sep=' ', timespec='minutes'))
        logger.info(f"Story {story_data.get('story_id')} 處理完成")
        return result
