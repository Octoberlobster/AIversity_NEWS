from typing import Optional, Dict, Any, List
import json
from datetime import datetime
from env import supabase, gemini_client

class TopicComprehensiveReporter:
    def __init__(self, supabase, gemini_client):
        self.supabase = supabase
        self.gemini_client = gemini_client
    
    def search_topic_by_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        根據關鍵字搜尋topic，取得topic_id和相關資訊
        Args:
            keyword: 搜尋關鍵字
        Returns:
            topic資訊字典，包含topic_id, topic_title等
        """
        try:
            response = self.supabase.table("topic").select("*").ilike("topic_title", f"%{keyword}%").execute()
            if response.data:
                return response.data[0]  # 返回第一個匹配的topic
            else:
                print(f"未找到包含關鍵字 '{keyword}' 的topic")
                return None
        except Exception as e:
            print(f"搜尋topic時發生錯誤: {e}")
            return None

    def get_all_topics(self) -> List[Dict[str, Any]]:
        """
        獲取所有topics
        Returns:
            所有topic的列表
        """
        try:
            response = self.supabase.table("topic").select("*").execute()
            return response.data
        except Exception as e:
            print(f"取得所有topics時發生錯誤: {e}")
            return []

    def get_story_ids_by_topic(self, topic_id: str) -> List[str]:
        """
        根據topic_id從topic_news_map表中取得所有相關的story_id
        Args:
            topic_id: topic的ID
        Returns:
            story_id列表
        """
        try:
            response = self.supabase.table("topic_news_map").select("story_id").eq("topic_id", topic_id).execute()
            return [item["story_id"] for item in response.data]
        except Exception as e:
            print(f"取得story_ids時發生錯誤: {e}")
            return []

    def get_news_data_by_story_ids(self, story_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根據story_id列表從single_news表中取得新聞資料
        Args:
            story_ids: story_id列表
        Returns:
            新聞資料列表
        """
        try:
            response = self.supabase.table("single_news").select(
                "news_title,short,category,generated_date,story_id,long"
            ).in_("story_id", story_ids).execute()
            return response.data
        except Exception as e:
            print(f"取得新聞資料時發生錯誤: {e}")
            return []

    def generate_comprehensive_report(self, topic_info: Dict[str, Any], news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        使用 Gemini API 生成綜合報導
        Args:
            topic_info: topic資訊
            news_data: 相關新聞資料
        Returns:
            綜合報導結果
        """
        # 準備新聞內容摘要
        news_summaries = []
        for news in news_data:
            summary = {
                "title": news.get("news_title", ""),
                "summary": news.get("short", ""),
                "category": news.get("category", ""),
                "date": news.get("generated_date", "")
            }
            news_summaries.append(summary)
        
        # 建立系統指令
        system_instruction = """
        你是一位專業的新聞編輯，負責將多篇相關新聞整合成一篇結構化的綜合報導。
        
        任務要求：
        1. 仔細分析所有提供的新聞內容
        2. 按時間順序梳理事件發展脈絡
        3. 提供客觀且平衡的觀點
        4. 嚴格按照指定的JSON格式輸出
        
        輸出格式必須包含以下四個部分：
        1. 主題標題（topic_title）：使用原始的topic標題
        2. 執行摘要（executive_summary）：150-200字的整體事件概述
        3. 背景與起源（background_and_origin）：300-400字，包含3-5個要點，說明事件如何開始、初始狀況、關鍵起始因素
        4. 目前發展（current_developments）：300-400字，包含3-5個要點，說明最新進展、近期動態、當前狀態
        
        請確保內容準確、語言流暢，並保持新聞報導的客觀性。
        """
        
        # 建立用戶提示
        user_prompt = f"""
        請根據以下資訊生成關於「{topic_info['topic_title']}」的結構化綜合報導：
        
        Topic資訊：
        - ID: {topic_info['topic_id']}
        - 標題: {topic_info['topic_title']}
        
        相關新聞數量: {len(news_data)}篇
        
        新聞摘要：
        {json.dumps(news_summaries, ensure_ascii=False, indent=2)}
        
        請嚴格按照以下JSON格式輸出綜合報導：
        
        {{
            "topic_title": "主題標題（使用原始topic_title）",
            "executive_summary": "150-200字的執行摘要，概述整個事件的核心要點",
            "background_and_origin": {{
                "content": "300-400字的背景與起源說明",
                "key_points": [
                    "要點1：事件的起始背景",
                    "要點2：最初的狀況分析", 
                    "要點3：關鍵的起始因素",
                    "要點4：相關的背景資訊",
                    "要點5：其他重要的起源因素"
                ]
            }},
            "current_developments": {{
                "content": "300-400字的目前發展狀況",
                "key_points": [
                    "要點1：最新的重要進展",
                    "要點2：近期的關鍵動態",
                    "要點3：當前狀態的分析",
                    "要點4：相關方的最新行動",
                    "要點5：未來可能的發展方向"
                ]
            }}
        }}
        
        注意：
        - 每個部分的key_points必須包含3-5個要點
        - 字數要求必須嚴格遵守
        - 內容必須基於提供的新聞資料
        - 保持客觀中立的新聞報導風格
        """
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                }
            )
            
            return json.loads(response.text)
        except Exception as e:
            print(f"生成綜合報導時發生錯誤: {e}")
            return None

    def save_comprehensive_report(self, topic_id: str, report_data: Dict[str, Any]) -> bool:
        """
        將綜合報導保存到資料庫
        Args:
            topic_id: topic ID
            report_data: 綜合報導資料
        Returns:
            是否成功保存
        """
        try:
            data_to_save = {
                "topic_id": topic_id,
                "report_content": json.dumps(report_data, ensure_ascii=False),
                "generated_date": datetime.now().isoformat(),
                "status": "completed"
            }
            
            response = self.supabase.table("comprehensive_reports").insert(data_to_save).execute()
            return True
        except Exception as e:
            print(f"保存綜合報導時發生錯誤: {e}")
            return False

    def process_single_topic(self, keyword: str = None, topic_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        處理單個topic的綜合報導
        Args:
            keyword: 搜尋關鍵字（如果沒有提供topic_info）
            topic_info: 直接提供的topic資訊
        Returns:
            處理結果
        """
        # 獲取topic資訊
        if not topic_info:
            if not keyword:
                return {"success": False, "error": "必須提供關鍵字或topic_info"}
            topic_info = self.search_topic_by_keyword(keyword)
            if not topic_info:
                return {"success": False, "error": f"找不到關鍵字 '{keyword}' 相關的topic"}
        
        topic_id = topic_info["topic_id"]
        topic_title = topic_info["topic_title"]
        
        print(f"處理Topic: {topic_title} (ID: {topic_id})")
        
        # 獲取相關story IDs
        story_ids = self.get_story_ids_by_topic(topic_id)
        if not story_ids:
            return {"success": False, "error": f"Topic '{topic_title}' 沒有相關的新聞"}
        
        print(f"找到 {len(story_ids)} 篇相關新聞")
        
        # 獲取新聞資料
        news_data = self.get_news_data_by_story_ids(story_ids)
        if not news_data:
            return {"success": False, "error": "無法獲取新聞資料"}
        
        # 生成綜合報導
        report = self.generate_comprehensive_report(topic_info, news_data)
        print(f"生成綜合報導結果: {report}")
        if not report:
            return {"success": False, "error": "生成綜合報導失敗"}
        
        # 保存報導
        # saved = self.save_comprehensive_report(topic_id, report)
        
        return {
            "success": True,
            "topic_id": topic_id,
            "topic_title": topic_title,
            "news_count": len(news_data),
            "report": report,
            # "saved": saved
        }

    def process_all_topics(self) -> List[Dict[str, Any]]:
        """
        處理所有topics的綜合報導
        Returns:
            所有處理結果的列表
        """
        # 獲取所有topics
        all_topics = self.get_all_topics()
        if not all_topics:
            print("沒有找到任何topics")
            return []
        
        print(f"找到 {len(all_topics)} 個topics，開始處理綜合報導...")
        
        results = []
        for i, topic_info in enumerate(all_topics, 1):
            print(f"\n進度: {i}/{len(all_topics)}")
            
            try:
                result = self.process_single_topic(topic_info=topic_info)
                results.append(result)
                
                if result["success"]:
                    print(f"✓ 成功生成綜合報導: {result['topic_title']}")
                else:
                    print(f"✗ 處理失敗: {result['error']}")
                    
            except Exception as e:
                error_result = {
                    "success": False,
                    "topic_id": topic_info.get("topic_id", "unknown"),
                    "topic_title": topic_info.get("topic_title", "unknown"),
                    "error": str(e)
                }
                results.append(error_result)
                print(f"✗ 處理異常: {str(e)}")
        
        return results

    def generate_summary_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成處理摘要報告
        Args:
            results: 所有處理結果
        Returns:
            摘要報告
        """
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        total_news = sum(r.get("news_count", 0) for r in successful)
        
        summary = {
            "total_topics": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_news_processed": total_news,
            "success_rate": f"{len(successful)/len(results)*100:.1f}%" if results else "0%",
            "failed_topics": [{"topic": r["topic_title"], "error": r["error"]} for r in failed]
        }
        
        return summary

# 使用範例
if __name__ == "__main__":
    # 初始化報導器
    reporter = TopicComprehensiveReporter(supabase, gemini_client)
    
    # 方法1: 處理單個topic（根據關鍵字）
    result = reporter.process_single_topic(keyword="AI人工智慧")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 方法2: 處理所有topics
    # results = reporter.process_all_topics()
    # summary = reporter.generate_summary_report(results)
    # print("處理摘要:")
    # print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    pass