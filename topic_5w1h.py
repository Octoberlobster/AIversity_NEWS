from env import supabase, gemini_client
from typing import List, Dict, Any, Optional
from google.genai import types
from pydantic import BaseModel
import json
import os
from datetime import datetime

class NodeDescription(BaseModel):
    """節點描述的資料結構"""
    id: str
    label: str
    description: str

class DetailedNodes(BaseModel):
    """詳細節點的資料結構"""
    who_nodes: List[NodeDescription]
    what_nodes: List[NodeDescription]
    when_nodes: List[NodeDescription]
    where_nodes: List[NodeDescription]
    why_nodes: List[NodeDescription]
    how_nodes: List[NodeDescription]

class Analysis5W1H(BaseModel):
    """5W1H分析結果的完整資料結構"""
    center_node: NodeDescription
    main_nodes: List[NodeDescription]
    detailed_nodes: DetailedNodes

class NewsAnalyzer:
    """新聞分析器類別"""
    
    def __init__(self):
        self.knowledge_base_dict = {
            "5W1H_Analysis": None,
            "search": None
        }
    
    def search_topic_by_keyword(self, keyword: str) -> Optional[Dict[str, Any]]:
        """
        根據關鍵字搜尋topic，取得topic_id和相關資訊
        
        Args:
            keyword: 搜尋關鍵字
            
        Returns:
            topic資訊字典，包含topic_id, topic_title等
        """
        try:
            # 在topic表中搜尋關鍵字
            response = supabase.table("topic").select("*").ilike("topic_title", f"%{keyword}%").execute()
            
            if response.data:
                return response.data[0]  # 返回第一個匹配的topic
            else:
                print(f"未找到包含關鍵字 '{keyword}' 的topic")
                return None
                
        except Exception as e:
            print(f"搜尋topic時發生錯誤: {e}")
            return None
    
    def get_story_ids_by_topic(self, topic_id: str) -> List[str]:
        """
        根據topic_id從topic_news_map表中取得所有相關的story_id
        
        Args:
            topic_id: topic的ID
            
        Returns:
            story_id列表
        """
        try:
            response = supabase.table("topic_news_map").select("story_id").eq("topic_id", topic_id).execute()
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
            response = supabase.table("single_news").select(
                "news_title,short,category,generated_date,story_id"
            ).in_("story_id", story_ids).execute()
            
            return response.data
            
        except Exception as e:
            print(f"取得新聞資料時發生錯誤: {e}")
            return []
    
    def get_topic_branches(self, topic_id: str) -> List[Dict[str, Any]]:
        """
        根據topic_id從topic_branch表中取得topic_branch_title
        
        Args:
            topic_id: topic的ID
            
        Returns:
            topic_branch資料列表
        """
        try:
            response = supabase.table("topic_branch").select("*").eq("topic_id", topic_id).execute()
            return response.data
            
        except Exception as e:
            print(f"取得topic_branch時發生錯誤: {e}")
            return []
    
    def format_news_data(self, news_list: List[Dict[str, Any]]) -> str:
        """
        將新聞資料格式化為文字
        
        Args:
            news_list: 新聞資料列表
            
        Returns:
            格式化後的新聞文字
        """
        if not news_list:
            return "目前沒有相關新聞資料。"
        
        news_text = "相關新聞資料：\n\n"
        for i, news in enumerate(news_list, 1):
            news_text += f"新聞 {i}：\n"
            news_text += f"標題：{news.get('news_title', 'N/A')}\n"
            news_text += f"摘要：{news.get('short', 'N/A')}\n"
            news_text += f"分類：{news.get('category', 'N/A')}\n"
            news_text += f"日期：{news.get('generated_date', 'N/A')}\n"
            news_text += f"故事ID：{news.get('story_id', 'N/A')}\n"
            news_text += "\n" + "-"*50 + "\n\n"
        
        return news_text
    
    def format_topic_branches(self, branches: List[Dict[str, Any]]) -> str:
        """
        將topic_branches格式化為文字
        
        Args:
            branches: topic_branch資料列表
            
        Returns:
            格式化後的branches文字
        """
        if not branches:
            return ""
        
        branches_text = "\n\n相關主題分支：\n"
        for branch in branches:
            branches_text += f"- {branch.get('topic_branch_title', 'N/A')}\n"
        
        return branches_text
    
    def set_knowledge_base_by_keyword(self, keyword: str, category: str = "5W1H_Analysis"):
        """
        根據關鍵字設定知識庫
        
        Args:
            keyword: 搜尋關鍵字
            category: 分析類型
        """
        # 1. 搜尋topic
        topic_info = self.search_topic_by_keyword(keyword)
        if not topic_info:
            print(f"無法找到關鍵字 '{keyword}' 相關的topic")
            return False, None, None
        
        topic_id = topic_info["topic_id"]
        topic_title = topic_info["topic_title"]
        
        # 2. 取得story_ids
        story_ids = self.get_story_ids_by_topic(topic_id)
        if not story_ids:
            print(f"topic_id '{topic_id}' 沒有相關的story")
            return False, None, None
        
        # 3. 取得新聞資料
        news_data = self.get_news_data_by_story_ids(story_ids)
        
        # 4. 取得topic_branches
        topic_branches = self.get_topic_branches(topic_id)
        
        # 5. 格式化資料
        news_text = self.format_news_data(news_data)
        branches_text = self.format_topic_branches(topic_branches)
        
        # 6. 設定知識庫
        if category == "search":
            self.knowledge_base_dict["search"] = f"""你是一個專業的新聞與專題 AI 助手，你目前的知識庫是：
主題：{topic_title}
{news_text}{branches_text}
需要時參考這些資料來回答問題。"""
        else:
            # 根據具體需求優化系統指令
            self.knowledge_base_dict["5W1H_Analysis"] = f"""你是一個專業的新聞與專題 AI 助手，專門提供某一事件或議題的5W1H分析。

請根據以下知識庫內容進行分析：

主題：{topic_title}
{news_text}{branches_text}

分析要求：
1. **What（什麼）**：topic_branch_title的內容，標題 + 80字左右敘述
2. **Where（哪裡）**：topic_branch_title提及的地點，標題 + 80字左右敘述
3. **Why（為什麼）**：為什麼會產生這個topic，150字敘述
4. **Who（誰）**：與topic有關的人及其重要關係，標題 + 80字左右敘述
5. **When（何時）**：topic_branch_title發生的時間軸
6. **How（如何）**：who中提及的人做了什麼事，標題 + 80字左右敘述

特別注意：
- detailed_nodes 中 what_nodes 的 label 必須使用原始的 topic_branch_title，不要修改
- 每個節點的描述要具體且完整
- 內容必須基於提供的知識庫資料
- 輸出格式必須是有效的JSON格式

分析結果需要包含三個層次：
1. 中心節點：主題的簡略概述
2. 5W1H主節點：六個主要分析維度的簡略描述  
3. 詳細節點：每個5W1H維度下的具體子項目"""
        
        return True, topic_branches, news_data
    
    def get_knowledge_base(self, category: str = "5W1H_Analysis") -> str:
        """
        取得知識庫內容
        
        Args:
            category: 分析類型
            
        Returns:
            知識庫的系統提示內容
        """
        if category in self.knowledge_base_dict and self.knowledge_base_dict[category]:
            return self.knowledge_base_dict[category]
        else:
            raise ValueError(f"Unknown category or empty knowledge base: {category}")
    
    def analyze_5W1H(self, keyword: str) -> Dict[str, Any]:
        """
        執行5W1H分析的主要函數
        
        Args:
            keyword: 要分析的關鍵字（例如："大罷免"）
            
        Returns:
            5W1H分析結果的字典
        """
        # 根據關鍵字設定知識庫
        success, topic_branches, news_data = self.set_knowledge_base_by_keyword(keyword, "5W1H_Analysis")
        if not success:
            return {"error": f"無法為關鍵字 '{keyword}' 設定知識庫"}
        
        try:
            # 取得系統提示
            system_instruction = self.get_knowledge_base("5W1H_Analysis")
            
            # 構建更詳細的用戶提示
            user_prompt = f"""請對關鍵字 '{keyword}' 相關的主題進行5W1H分析。

分析時請特別注意：
1. What節點：使用所有的topic_branch_title作為標題，並提供80字左右的敘述
2. Where節點：從topic_branch_title中識別地點，提供標題和80字敘述
3. Why節點：分析為什麼會產生這個topic，提供150字敘述
4. Who節點：識別與topic相關的重要人物，說明其關係，提供標題和80字敘述
5. When節點：分析topic_branch_title發生的時間軸
6. How節點：分析who中提及的人做了什麼事，提供標題和80字敘述

請確保detailed_nodes中what_nodes的label直接使用原始的topic_branch_title。"""
            
            # 讓AI進行5W1H分析
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=Analysis5W1H,
                )
            )
            
            # 解析結果
            analysis_result = response.parsed
            result_dict = {
                "center_node": {
                    "id": analysis_result.center_node.id,
                    "label": analysis_result.center_node.label,
                    "description": analysis_result.center_node.description
                },
                "main_nodes": [
                    {
                        "id": node.id,
                        "label": node.label, 
                        "description": node.description
                    } for node in analysis_result.main_nodes
                ],
                "detailed_nodes": {
                    "who_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.who_nodes
                    ],
                    "what_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.what_nodes
                    ],
                    "when_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.when_nodes
                    ],
                    "where_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.where_nodes
                    ],
                    "why_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.why_nodes
                    ],
                    "how_nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "description": node.description
                        } for node in analysis_result.detailed_nodes.how_nodes
                    ]
                },
                # 添加原始資料以供參考
                # "metadata": {
                #     "topic_branches": topic_branches,
                #     "news_count": len(news_data) if news_data else 0,
                #     "analysis_date": datetime.now().isoformat()
                # }
            }
            
            # 儲存到JSON檔案
            self.save_analysis_result(keyword, result_dict)
            
            return result_dict
            
        except Exception as e:
            print(f"5W1H分析時發生錯誤: {e}")
            return {"error": str(e)}
    
    def save_analysis_result(self, keyword: str, result: Dict[str, Any]):
        """
        儲存分析結果到JSON檔案
        
        Args:
            keyword: 關鍵字
            result: 分析結果
        """
        try:
            output_folder = "json/5W1H"
            os.makedirs(output_folder, exist_ok=True)
            
            # 使用時間戳記避免檔名衝突
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = keyword.replace(' ', '_').replace('/', '_')
            filename = f"{output_folder}/{safe_keyword}_5W1H_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"5W1H分析結果已儲存至: {filename}")
            
        except Exception as e:
            print(f"儲存檔案時發生錯誤: {e}")
    
    def search_and_analyze(self, keyword: str) -> Dict[str, Any]:
        """
        完整的搜尋和分析流程
        
        Args:
            keyword: 搜尋關鍵字
            
        Returns:
            完整的分析結果，包含topic資訊和5W1H分析
        """
        # 1. 搜尋topic
        topic_info = self.search_topic_by_keyword(keyword)
        if not topic_info:
            return {"error": f"未找到關鍵字 '{keyword}' 相關的主題"}
        
        # 2. 執行5W1H分析
        analysis_result = self.analyze_5W1H(keyword)
        
        # 3. 整合結果
        complete_result = {
            "keyword": keyword,
            "topic_info": topic_info,
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
        
        return complete_result
    
    def batch_analyze_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """
        批次分析多個關鍵字
        
        Args:
            keywords: 關鍵字列表
            
        Returns:
            批次分析結果
        """
        results = {}
        
        for keyword in keywords:
            print(f"正在分析關鍵字: {keyword}")
            results[keyword] = self.search_and_analyze(keyword)
        
        return results
    
    def validate_analysis_result(self, result: Dict[str, Any]) -> bool:
        """
        驗證分析結果是否符合要求
        
        Args:
            result: 分析結果
            
        Returns:
            是否符合要求
        """
        try:
            # 檢查基本結構
            required_keys = ["center_node", "main_nodes", "detailed_nodes"]
            for key in required_keys:
                if key not in result:
                    print(f"缺少必要欄位: {key}")
                    return False
            
            # 檢查detailed_nodes結構
            detailed_keys = ["who_nodes", "what_nodes", "when_nodes", "where_nodes", "why_nodes", "how_nodes"]
            for key in detailed_keys:
                if key not in result["detailed_nodes"]:
                    print(f"缺少detailed_nodes欄位: {key}")
                    return False
            
            # 檢查what_nodes是否包含topic_branch_title
            what_nodes = result["detailed_nodes"]["what_nodes"]
            if not what_nodes:
                print("what_nodes為空")
                return False
            
            print("分析結果驗證通過")
            return True
            
        except Exception as e:
            print(f"驗證分析結果時發生錯誤: {e}")
            return False

# 使用範例和測試函數
def main():
    """主要執行函數"""
    analyzer = NewsAnalyzer()
    
    # 單一關鍵字分析
    keyword = "京華城案"
    print(f"開始分析關鍵字: {keyword}")
    result = analyzer.search_and_analyze(keyword)
    
    if "error" not in result:
        analysis = result['analysis']
        
        print("\n=== 分析結果 ===")
        print(f"主題: {result['topic_info'].get('topic_title', 'N/A')}")
        print(f"中心節點: {analysis['center_node']['label']}")
        print(f"描述: {analysis['center_node']['description']}")
        
        print("\n=== 5W1H主要節點 ===")
        for node in analysis['main_nodes']:
            print(f"- {node['label']}: {node['description']}")
        
        print("\n=== 詳細節點示例（What） ===")
        for node in analysis['detailed_nodes']['what_nodes']:
            print(f"- {node['label']}: {node['description']}")
            
        # 驗證結果
        analyzer.validate_analysis_result(analysis)
        
    else:
        print(f"分析失敗: {result['error']}")

def demo_with_custom_requirements():
    """
    按照具體需求進行演示的函數
    """
    analyzer = NewsAnalyzer()
    keyword = "川普關稅戰"  # 你可以改成其他關鍵字
    
    print(f"開始按照自定義需求分析關鍵字: {keyword}")
    
    # 1. 設定知識庫
    success, topic_branches, news_data = analyzer.set_knowledge_base_by_keyword(keyword)
    if not success:
        print(f"無法設定知識庫")
        return
    
    print(f"找到 {len(topic_branches)} 個主題分支")
    print(f"找到 {len(news_data)} 條相關新聞")
    
    # 2. 執行分析
    analysis_result = analyzer.analyze_5W1H(keyword)
    
    if "error" not in analysis_result:
        print("\n=== 分析成功 ===")
        
        # 顯示What節點（應該包含所有topic_branch_title）
        print("\n=== What節點（Topic Branch Titles） ===")
        for node in analysis_result['detailed_nodes']['what_nodes']:
            print(f"標題: {node['label']}")
            print(f"描述: {node['description']}")
            print("-" * 40)
        
        # 顯示其他重要節點
        print("\n=== Why節點（150字敘述） ===")
        for node in analysis_result['detailed_nodes']['why_nodes']:
            print(f"描述: {node['description']}")
        
        print("\n=== 時間軸（When） ===")
        for node in analysis_result['detailed_nodes']['when_nodes']:
            print(f"時間: {node['label']}")
            print(f"描述: {node['description']}")
            
    else:
        print(f"分析失敗: {analysis_result['error']}")

if __name__ == "__main__":
    # 方法1: 標準分析
    main()
    
    print("\n" + "="*80 + "\n")
    
    # 方法2: 按照自定義需求分析
    demo_with_custom_requirements()