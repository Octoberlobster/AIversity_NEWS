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
        你是一位資深新聞編輯，專長是撰寫專題報導的深度分析。
        請嚴格遵守：
        1) 所有回覆必須以 Markdown 輸出（標題、粗體、清單、表格皆可視需要使用）。
        2) 風格：專業、中立、條理清晰；盡量以可驗證的事實為基礎。
        3) 僅能使用我提供的資料進行分析與推論；不得臆測或補完未提供的資訊。
        4) 若資料不足以支持某段分析，請在該處以「**資料不足**」標註，並簡述還需要哪些資訊。
        5) 章節名稱與組織方式可自行決定，但需涵蓋：背景脈絡、核心議題、多方觀點、影響/趨勢、未來可能走向（名稱可變）。
        6) 優先輸出可讀性高的結構（標題層級清楚、重點條列、關鍵數字置於醒目位置）。


        """
        
        # 建立用戶提示
        user_prompt = f"""
        以下是新聞資料，請根據內容撰寫一份專題報導的深度分析報告（Markdown 格式）。

        【Topic 資訊】
        - ID: {topic_info['topic_id']}
        - 標題: {topic_info['topic_title']}

        【相關新聞摘要（JSON）】
        {json.dumps(news_summaries, ensure_ascii=False, indent=2)}

        請注意：
        - 可自由決定章節與結構，但務必讓讀者能快速掌握全貌與爭點。
        - 儘量整合多篇新聞的脈絡與關聯性，避免逐篇流水帳。
        - 如需引用數據或時間點，請盡量在文中以括號標示其來自哪一則摘要（例如：#3、#7）。
        - 若能提煉出「關鍵時間線」或「利害關係人地圖」，可放在文末作為附錄（選用）。

        """
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.3,
                }
            )

            return response.text
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
    result = reporter.process_single_topic(keyword="重啟核三公投")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 方法2: 處理所有topics
    # results = reporter.process_all_topics()
    # summary = reporter.generate_summary_report(results)
    # print("處理摘要:")
    # print(json.dumps(summary, ensure_ascii=False, indent=2))
    
    pass