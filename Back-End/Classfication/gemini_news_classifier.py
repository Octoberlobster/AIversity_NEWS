"""
Gemini 新聞分類器
使用 Google Gemini 2.5 Flash Lite 進行智慧新聞分類

兩階段分類策略：
1. Topic → Category：判斷 topic 屬於哪個新聞類別
2. News → Topic：將該類別的新聞分配到 topic 中
"""

import os
import logging
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 定義回應結構
class CategoryClassificationResult(BaseModel):
    """Topic 分類結果的結構（支援多類別）"""
    primary_category: str
    secondary_categories: List[str]
    reason: str


class NewsClassificationResult(BaseModel):
    """新聞分類結果的結構"""
    related_news_ids: List[int]
    reason: str


class GeminiNewsClassifier:
    """基於 Gemini 的新聞分類器"""
    
    def __init__(self):
        """初始化分類器"""
        # 初始化 Supabase 客戶端
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # 初始化 Gemini
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # 預定義的新聞分類
        self.categories = [
            "Politics",
            "Taiwan News", 
            "International News",
            "Science & Technology",
            "Lifestyle & Consumer",
            "Sports",
            "Entertainment", 
            "Business & Finance",
            "Health & Wellness"
        ]
    
    # ========== 輔助方法 ==========
    
    def _clean_json_response(self, response: str) -> str:
        """清理 Gemini 回應中的 markdown 格式標記和其他問題"""
        import re
        
        # 移除 ```json 和 ``` 標記
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]  # 移除 ```json
        if response.startswith('```'):
            response = response[3:]   # 移除 ```
        if response.endswith('```'):
            response = response[:-3]  # 移除結尾的 ```
        
        response = response.strip()
        
        # 處理 JSON 字串中的問題
        try:
            # 尋找 JSON 物件的開始和結束
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_part = response[start_idx:end_idx+1]
                
                # 清理引號問題 - 將智慧引號替換為標準引號
                json_part = json_part.replace('"', '"').replace('"', '"')
                json_part = json_part.replace(''', "'").replace(''', "'")
                
                # 處理可能的換行問題
                json_part = re.sub(r'\n\s*', ' ', json_part)
                
                return json_part
            
        except Exception as e:
            logger.warning(f"清理 JSON 時發生問題: {e}")
        
        return response
    
    def _extract_category_from_text(self, text: str) -> str:
        """從文本中提取 category，作為 JSON 解析失敗時的備用方法"""
        text_lower = text.lower()
        
        # 檢查每個類別是否出現在文本中
        for category in self.categories:
            # 檢查完整的類別名稱
            if category.lower() in text_lower:
                return category
            
            # 檢查類別的關鍵字
            category_keywords = {
                "Politics": ["politics", "political", "政治"],
                "Taiwan News": ["taiwan", "台灣", "臺灣"],
                "International News": ["international", "world", "global", "國際"],
                "Science & Technology": ["technology", "science", "tech", "科技", "科學"],
                "Lifestyle & Consumer": ["lifestyle", "consumer", "生活"],
                "Sports": ["sports", "sport", "運動", "體育"],
                "Entertainment": ["entertainment", "娛樂"],
                "Business & Finance": ["business", "finance", "financial", "商業", "金融", "經濟", "貿易"],
                "Health & Wellness": ["health", "wellness", "醫療", "健康"]
            }
            
            keywords = category_keywords.get(category, [])
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        
        return "其他"
    
    # ========== 主要分類方法 ==========
    
    def step1_classify_topic_to_category(self, topic_title: str) -> tuple[List[str], str]:
        """
        步驟1：將 topic 分類到多個 category (使用 Google 搜尋增強分類準確性)
        
        Args:
            topic_title: topic 標題
            
        Returns:
            tuple: (分類的 categories 列表, 分類理由)
        """
        try:
            prompt = self._build_topic_classification_prompt(topic_title, None)
            # 暫時不使用結構化輸出，先用搜尋功能但返回普通文本
            response = self._call_gemini_with_search_text(prompt)
            
            # 清理和解析結構化回應
            try:
                cleaned_response = self._clean_json_response(response)
                result = json.loads(cleaned_response)
                
                primary_category = result.get("primary_category", result.get("category", "其他"))
                secondary_categories = result.get("secondary_categories", [])
                if not isinstance(secondary_categories, list):
                    secondary_categories = []
                reason = result.get("reason", "無法判斷")
                
                # 合併主要和次要類別
                all_categories = [primary_category] + secondary_categories
                all_categories = list(dict.fromkeys(all_categories))  # 去重但保持順序
                
                logger.info(f"Topic '{topic_title}' 分類為: {all_categories}, 理由: {reason}")
                return all_categories, reason
                
            except json.JSONDecodeError as e:
                logger.error(f"無法解析 Gemini 結構化回應: {response}")
                logger.error(f"JSON 解析錯誤: {e}")
                
                # 備用解析：嘗試從回應中提取 category
                try:
                    category = self._extract_category_from_text(response)
                    if category != "其他":
                        logger.info(f"使用備用解析成功提取 category: {category}")
                        return [category], "透過備用解析取得"
                except Exception as parse_error:
                    logger.error(f"備用解析也失敗: {parse_error}")
                
                # 如果都失敗了，強制分類到最合適的默認類別
                default_categories = self._get_default_categories(topic_title)
                return default_categories, "使用默認分類"
                
        except Exception as e:
            logger.error(f"步驟1分類失敗: {e}")
            # 即使發生錯誤，也要嘗試分類到合適的默認類別
            default_categories = self._get_default_categories(topic_title)
            return default_categories, "發生錯誤，使用默認分類"
    
    def _get_default_categories(self, topic_title: str) -> List[str]:
        """根據 topic 標題獲取默認分類，支援多類別分類"""
        topic_lower = topic_title.lower()
        categories = []
        
        # 基本關鍵字映射到我們的 9 個類別
        if any(word in topic_lower for word in ['川普', 'trump', '選舉', '政治', '公投', '立院', '政府']):
            categories.append("Politics")
        elif any(word in topic_lower for word in ['台灣', '柯文哲', '蔡英文', '韓國瑜', '本土']):
            categories.append("Taiwan News")
        elif any(word in topic_lower for word in ['國際', '美國', '中國', '俄烏', '以色列', '伊朗', '泰柬', '戰爭', '衝突']):
            categories.append("International News")
        elif any(word in topic_lower for word in ['科技', '科學', 'ai', '人工智慧', '晶片', '半導體']):
            categories.append("Science & Technology")
        elif any(word in topic_lower for word in ['生活', '消費', '購物', '美食', '旅遊', '展覽']):
            categories.append("Lifestyle & Consumer")
        elif any(word in topic_lower for word in ['運動', '體育', '球賽', '奧運', '世界盃']):
            categories.append("Sports")
        elif any(word in topic_lower for word in ['娛樂', '電影', '音樂', '明星', '演員']):
            categories.append("Entertainment")
        elif any(word in topic_lower for word in ['經濟', '金融', '股市', '投資', '貿易', 'GDP', '通膨']):
            categories.append("Business & Finance")
        elif any(word in topic_lower for word in ['健康', '醫療', '疫情', '病毒', '疫苗']):
            categories.append("Health & Wellness")
        
        # 如果沒有匹配到任何類別，返回預設
        return categories if categories else ["其他"]
    
    def step2_classify_news_to_topic(self, categories: List[str], topic_info: Dict, topic_content: str = None) -> List[Dict]:
        """
        步驟2：將多個類別的新聞分配到 topic
        
        Args:
            categories: 新聞類別列表
            topic_info: topic 資訊
            topic_content: topic 的詳細內容/理由 (來自步驟1的分類理由)
            
        Returns:
            符合該 topic 的新聞列表
        """
        try:
            all_classified_news = []
            
            # 對每個類別進行新聞分類
            for category in categories:
                logger.info(f"處理類別 '{category}' 的新聞...")
                
                # 1. 獲取該類別的新聞
                news_list = self._get_news_by_category(category)
                
                if not news_list:
                    logger.info(f"在類別 '{category}' 中沒有找到新聞")
                    continue
                
                logger.info(f"找到 {len(news_list)} 則 '{category}' 類別的新聞")
                
                # 2. 一次處理所有新聞
                classified_news = self._classify_news_batch(news_list, topic_info, topic_content)
                
                if classified_news:
                    all_classified_news.extend(classified_news)
                    logger.info(f"從 '{category}' 類別分類 {len(classified_news)} 則新聞到 topic '{topic_info['topic_title']}'")
            
            # 去重（避免同一則新聞出現在多個類別中）
            unique_news = {}
            for news in all_classified_news:
                news_id = news.get('story_id')
                if news_id not in unique_news:
                    unique_news[news_id] = news
            
            final_news_list = list(unique_news.values())
            logger.info(f"總共成功分類 {len(final_news_list)} 則新聞到 topic '{topic_info['topic_title']}'")
            return final_news_list
            
        except Exception as e:
            logger.error(f"步驟2分類失敗: {e}")
            return []
    
    def classify_all_topics(self) -> List[Dict]:
        """對所有 topic 進行批量分類"""
        try:
            # 一次性獲取所有 topic 資料
            logger.info("開始獲取所有 topics...")
            all_topics = self._get_all_topics()
            
            if not all_topics:
                logger.warning("沒有找到任何 topics")
                return []
                
            logger.info(f"成功獲取 {len(all_topics)} 個 topics，開始逐一分類...")
            
            results = []
            for idx, topic in enumerate(all_topics, 1):
                logger.info(f"處理第 {idx}/{len(all_topics)} 個 topic: {topic['topic_title']}")
                
                try:
                    # 直接在這裡執行完整的分類流程
                    topic_info = topic  # 已經有完整資訊了
                    
                    # 步驟1：判斷 topic 屬於哪些 category，並獲取分類理由
                    logger.info(f"開始步驟1：為 topic '{topic_info['topic_title']}' 分類")
                    categories, reason = self.step1_classify_topic_to_category(topic_info["topic_title"])

                    # 步驟2：將多個 category 的新聞分到 topic 中，使用步驟1的理由作為 topic_content
                    categories_str = ', '.join(categories)
                    logger.info(f"開始步驟2：在類別 '{categories_str}' 中尋找相關新聞 (使用理由: {reason[:50]}...)")
                    classified_news = self.step2_classify_news_to_topic(categories, topic_info, reason)
                    
                    # 儲存分類結果（可選）
                    if classified_news:
                        self._save_classification_results(topic["topic_id"], classified_news)
                    
                    result = {
                        "topic_id": topic_info["topic_id"],
                        "topic_title": topic_info["topic_title"], 
                        "source_story": [
                            {
                                "story_id": news["story_id"],
                                "story_title": news["news_title"]
                            }
                            for news in classified_news
                        ],
                        "success": True
                    }
                    results.append(result)
                    
                    # 避免 API 頻率限制
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"處理 topic {topic['topic_id']} 失敗: {e}")
                    results.append({
                        "topic_id": topic["topic_id"],
                        "topic_title": topic["topic_title"],
                        "source_story": [],
                        "success": False,
                        "error": str(e)
                    })
            
            # 統計結果
            success_count = sum(1 for r in results if r.get("success"))
            total_news_classified = sum(len(r.get("source_story", [])) for r in results if r.get("success"))
            
            logger.info(f"批量分類完成！成功: {success_count}/{len(results)}, 總共分類了 {total_news_classified} 則新聞")
            
            return results
            
        except Exception as e:
            logger.error(f"批量分類失敗: {e}")
            return []
    
    # ========== 資料庫操作方法 ==========
    
    def _get_all_topics(self) -> List[Dict]:
        """一次性獲取所有 topic 資訊"""
        try:
            response = self.supabase.table("topic").select(
                "topic_id, topic_title"
            ).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"獲取所有 topics 失敗: {e}")
            return []
    
    def _get_news_by_category(self, category: str) -> List[Dict]:
        """獲取指定類別的新聞"""
        try:
            response = self.supabase.table("single_news").select(
                "story_id, news_title, short, category"
            ).eq("category", category).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"獲取新聞資料失敗: {e}")
            return []
    
    def _save_classification_results(self, topic_id: str, classified_news: List[Dict]):
        """儲存分類結果到資料庫"""
        try:
            logger.info(f"儲存分類結果：topic_id={topic_id}, 新聞數量={len(classified_news)}")
            
            # TODO: 實現儲存邏輯
            # 可以儲存到 topic_branch_news_map 或其他相關表格
            
        except Exception as e:
            logger.error(f"儲存分類結果失敗: {e}")
    
    # ========== Gemini API 相關方法 ==========
    
    def _call_gemini_async(self, prompt: str, response_schema=None) -> str:
        """同步呼叫 Gemini API，支援結構化輸出"""
        try:
            from google.genai import types
            
            if response_schema:
                # 使用結構化輸出
                config = types.GenerateContentConfig(
                    response_schema=response_schema,
                    response_mime_type="application/json"  # 強制回傳 JSON 格式
                )
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-lite",  # 結構化輸出需要 2.5 版本
                    contents=prompt,
                    config=config
                )
            else:
                # 一般模式
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt
                )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API 呼叫失敗: {e}")
            raise
    
    def _call_gemini_with_search_text(self, prompt: str) -> str:
        """同步呼叫 Gemini API 並啟用 Google 搜尋功能，返回純文本"""
        try:
            from google.genai import types
            
            # 定義 Google 搜尋工具
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            # 設定生成配置 - 只使用搜尋工具
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API (with search text) 呼叫失敗: {e}")
            # 如果搜尋功能失敗，回退到一般模式
            logger.info("回退到一般模式...")
            return self._call_gemini_async(prompt)

    def _call_gemini_with_search(self, prompt: str, response_schema=None) -> str:
        """同步呼叫 Gemini API 並啟用 Google 搜尋功能，支援結構化輸出"""
        try:
            from google.genai import types
            
            # 定義 Google 搜尋工具
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            # 設定生成配置 - 注意：使用工具時不能設定 response_mime_type
            if response_schema:
                config = types.GenerateContentConfig(
                    tools=[grounding_tool],
                    response_schema=response_schema
                    # 不設定 response_mime_type，因為與工具不相容
                )
            else:
                config = types.GenerateContentConfig(
                    tools=[grounding_tool]
                )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",  # 使用支援搜尋和結構化輸出的模型
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API (with search) 呼叫失敗: {e}")
            # 如果搜尋功能失敗，回退到一般模式
            logger.info("回退到一般模式...")
            return self._call_gemini_async(prompt, response_schema)
    
    def _build_topic_classification_prompt(self, topic_title: str, topic_content: str = None) -> str:
        """構建 topic 分類的 prompt，支援多類別分類"""
        prompt = f"""你是一個專業的新聞分類專家。我需要你根據 topic 資訊，判斷它最適合歸類到哪些新聞類別。

請先搜尋關於這個 topic 的最新資訊，了解它的背景和性質，然後進行分類。

Topic 標題：{topic_title}"""
        
        if topic_content:
            prompt += f"\nTopic 內容：{topic_content}"
        
        prompt += f"""

⚠️ **重要：你必須從以下 9 個類別中選擇，不可以使用其他類別名稱**：
{', '.join(self.categories)}

請執行以下步驟：
1. 搜尋這個 topic 的相關資訊和最新發展
2. 分析 topic 的主要內容和性質
3. **選擇一個主要類別和最多兩個次要相關類別**
4. 說明選擇的理由

**分類原則**：
- primary_category：最主要相關的類別（必須）
- secondary_categories：次要相關的類別（最多2個，可為空）
- 一個 topic 可能涉及多個類別，例如「川普關稅戰」可能同時涉及 "International News" 和 "Business & Finance"
- 「颱風楊柳」可能同時涉及 "Taiwan News" 和可能的其他影響

請以 JSON 格式回應：
{{
    "primary_category": "從上述9個類別中選擇的主要類別名稱（必須完全一致）",
    "secondary_categories": ["從上述9個類別中選擇的次要類別（可為空數組，最多2個）"],
    "reason": "選擇理由，包含搜尋到的相關資訊"
}}"""
        
        return prompt
    
    def _build_news_classification_prompt(self, news_list_str: str, topic_info: Dict, topic_content: str = None) -> str:
        """構建新聞分類的 prompt，配合結構化輸出"""
        # 組合 Topic 資訊
        topic_section = f"Topic 資訊：\n標題：{topic_info['topic_title']}"
        
        # 如果有 topic_content，加入更詳細的描述
        if topic_content:
            topic_section += f"\n詳細描述：{topic_content}"
        
        return f"""你是一個專業的新聞分析專家。請判斷以下新聞中，哪些與給定的 Topic 直接相關。

{topic_section}

待分析的新聞：
{news_list_str}

🎯 **核心原則**：只有直接討論該 Topic 的新聞才算相關

📋 **具體匹配標準**：
1. **字面匹配**：新聞標題或內容必須包含 Topic 的核心關鍵字
2. **主題一致**：新聞的主要討論內容必須是該 Topic
3. **避免聯想**：不要因為間接關聯就認為相關

⚠️ **嚴格限制**：
- 「二戰終戰80週年」→ 只能是關於日本終戰日、靖國神社、二戰紀念等直接相關的新聞
- 「重啟核三公投」→ 只能是關於核電廠、核三、公投、能源政策等直接相關的新聞
- 「京華城案」→ 只能是關於柯文哲、京華城、司法案件等直接相關的新聞
- 「颱風楊柳」→ 只能是關於楊柳颱風的天氣新聞

🚫 **絕對排除**：
- 僅是同類別但不同主題的新聞（如不同颱風、不同案件、不同戰爭）
- 需要多層推理才能關聯的新聞
- 僅是背景相同但主題不同的新聞

請嚴格按照字面意思進行匹配，不要過度解釋或聯想。

        請回應與 Topic 直接相關的新聞編號列表和簡潔理由。"""
    
    def _classify_news_batch(self, news_batch: List[Dict], topic_info: Dict, topic_content: str = None) -> List[Dict]:
        """對一批新聞進行分類判斷，使用結構化輸出"""
        try:
            # 構建新聞列表字串
            news_list_str = ""
            for idx, news in enumerate(news_batch):
                news_title = news.get('news_title', '無標題')
                news_short = news.get('short', '無內容')[:200]
                news_list_str += f"{idx+1}. 標題：{news_title}\n   內容：{news_short}...\n\n"
            
            # 構建並發送 prompt，使用結構化輸出並傳入 topic_content
            prompt = self._build_news_classification_prompt(news_list_str, topic_info, topic_content)
            response = self._call_gemini_async(prompt, NewsClassificationResult)
            
            # 解析結構化回應
            try:
                result = json.loads(response)
                related_news = []
                
                # 處理 related_news_ids 列表
                related_news_ids = result.get("related_news_ids", [])
                reason = result.get("reason", "無分類理由")
                
                for news_index in related_news_ids:
                    # 轉換為 0-based index
                    array_index = news_index - 1
                    if 0 <= array_index < len(news_batch):
                        news_data = news_batch[array_index].copy()
                        news_data.update({
                            "reason": reason,
                            "topic_id": topic_info["topic_id"]
                        })
                        related_news.append(news_data)
                
                return related_news
                
            except json.JSONDecodeError:
                logger.error(f"無法解析分類結構化回應: {response}")
                return []
                
        except Exception as e:
            logger.error(f"批次分類失敗: {e}")
            return []
    
    # ========== 統計報告方法 ==========
    
    def generate_classification_report(self, results: List[Dict]) -> Dict:
        """生成分類結果統計報告"""
        if not results:
            return {"message": "沒有分類結果"}
        
        # 統計基本資訊
        total_topics = len(results)
        successful_classifications = [r for r in results if r.get("success")]
        failed_classifications = [r for r in results if not r.get("success")]
        
        # 統計總新聞數
        total_news_classified = 0
        topics_with_news = 0
        
        for result in successful_classifications:
            news_count = len(result.get("source_story", []))
            total_news_classified += news_count
            if news_count > 0:
                topics_with_news += 1
        
        report = {
            "summary": {
                "total_topics": total_topics,
                "successful_classifications": len(successful_classifications),
                "failed_classifications": len(failed_classifications),
                "success_rate": f"{len(successful_classifications)/total_topics*100:.1f}%",
                "topics_with_news": topics_with_news,
                "topics_without_news": len(successful_classifications) - topics_with_news,
                "total_news_classified": total_news_classified,
                "average_news_per_topic": f"{total_news_classified/len(successful_classifications):.1f}" if successful_classifications else "0"
            },
            "failed_topics": [
                {
                    "topic_id": r.get("topic_id", "未知"),
                    "topic_title": r.get("topic_title", "未知"),
                    "error": r.get("error", "未知錯誤")
                }
                for r in failed_classifications
            ]
        }
        
        return report

    def format_results_for_display(self, results: List[Dict]) -> List[Dict]:
        """格式化結果以便清楚顯示"""
        formatted_results = []
        
        for result in results:
            if result.get("success"):
                formatted_result = {
                    "topic_id": result["topic_id"],
                    "topic_title": result["topic_title"],
                    "source_story": result["source_story"]
                }
            else:
                formatted_result = {
                    "topic_id": result["topic_id"],
                    "topic_title": result["topic_title"],
                    "source_story": [],
                    "error": result.get("error", "未知錯誤")
                }
            
            formatted_results.append(formatted_result)
        
        return formatted_results


# ========== 主程式 ==========

def main():
    """主函數，用於測試分類器"""
    classifier = GeminiNewsClassifier()
    
    print("=== Gemini 新聞分類器 ===")
    print("初始化完成！")
    print("\n主要功能：")
    print("1. classifier.classify_all_topics() - 批量分類所有 topics")
    print("2. classifier.generate_classification_report(results) - 生成統計報告")
    print("\n範例程式碼（取消註解以執行）：")
    print("# 批量分類所有 topics")
    print("# results = await classifier.classify_all_topics()")
    print("# report = classifier.generate_classification_report(results)")
    print("# print(json.dumps(report, ensure_ascii=False, indent=2))")
    print("\n開始執行批量分類...")
    
    # 直接執行批量分類
    try:
        results = classifier.classify_all_topics()
        
        # 格式化結果以便清楚顯示
        formatted_results = classifier.format_results_for_display(results)
        
        print("\n" + "="*50)
        print("分類結果（清楚格式）：")
        print("="*50)
        
        # 顯示前幾個結果作為範例
        for i, result in enumerate(formatted_results[:5]):  # 顯示前5個作為範例
            print(f"\n--- Topic {i+1} ---")
            print(f"Topic ID: {result['topic_id']}")
            print(f"Topic Title: {result['topic_title']}")
            print(f"Source Story Count: {len(result['source_story'])}")
            
            if result['source_story']:
                print("Source Stories:")
                for j, story in enumerate(result['source_story'][:5]):  # 只顯示前5則新聞
                    print(f"  {j+1}. Story ID: {story['story_id']}")
                    print(f"     Story Title: {story['story_title']}")
            else:
                print("Source Stories: 無相關新聞")
        
        if len(formatted_results) > 5:
            print(f"\n... 還有 {len(formatted_results) - 5} 個 topics（完整結果請查看統計報告）")
        
        # 生成統計報告
        report = classifier.generate_classification_report(results)
        print("\n" + "="*50)
        print("統計報告：")
        print("="*50)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        
        # 保存結果為 JSON 檔案
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_topics": len(results),
            "classification_results": formatted_results,
            "statistics": report
        }
        
        # 輸出檔案名稱包含時間戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"classification_results_{timestamp}.json"
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 分類結果已保存至: {output_filename}")
        except Exception as e:
            logger.error(f"保存 JSON 檔案失敗: {e}")
            print(f"❌ 保存檔案失敗: {e}")
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"執行批量分類失敗: {e}")
        print(f"執行失敗: {e}")
        return []


if __name__ == "__main__":
    main()
