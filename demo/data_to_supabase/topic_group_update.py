"""
新聞分支更新器
當偵測到新新聞時，自動將其分配到合適的分支，或歸入「其他新聞」分支
"""

import os
import sys
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("錯誤：請在 .env 檔案中設定 SUPABASE_URL 與 SUPABASE_KEY")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("錯誤：請在 .env 檔案中設定 GEMINI_API_KEY")
    sys.exit(1)

try:
    from supabase import create_client
    print("✓ Supabase 套件已載入")
except ImportError:
    print("請先安裝 supabase-py：pip install supabase")
    sys.exit(1)

try:
    import google.genai as genai
    from google.genai import types
    print("✓ Google Genai 套件已載入")
except ImportError:
    print("請先安裝 google-genai SDK：pip install google-generativeai")
    sys.exit(1)


class NewsBranchUpdater:
    """新聞分支更新器"""
    
    def __init__(self):
        """初始化客戶端"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            print("✓ Gemini Client 初始化成功")
        except Exception as e:
            print(f"✗ Gemini Client 初始化失敗: {e}")
            self.genai_client = None
    
    def fetch_new_news(self, topic_id):
        """
        獲取指定主題中尚未分配到分支的新聞
        
        Args:
            topic_id: 主題ID
            
        Returns:
            未分配的新聞列表
        """
        try:
            print(f"\n檢查主題 {topic_id} 的新聞...")
            
            # 1. 獲取該主題下所有新聞
            topic_news_response = self.supabase.table('topic_news_map').select(
                'story_id'
            ).eq('topic_id', topic_id).execute()
            
            if not topic_news_response.data:
                print(f"  主題 {topic_id} 沒有任何新聞")
                return []
            
            topic_story_ids = {item['story_id'] for item in topic_news_response.data}
            print(f"  主題總新聞數: {len(topic_story_ids)}")
            
            # 2. 獲取該主題下所有分支
            branches_response = self.supabase.table('topic_branch').select(
                'topic_branch_id'
            ).eq('topic_id', topic_id).execute()
            
            if not branches_response.data:
                print(f"  主題 {topic_id} 沒有任何分支")
                # 所有新聞都是未分配的
                return self._fetch_news_details(list(topic_story_ids))
            
            branch_ids = [item['topic_branch_id'] for item in branches_response.data]
            print(f"  主題分支數: {len(branch_ids)}")
            
            # 3. 獲取已分配到分支的新聞
            assigned_response = self.supabase.table('topic_branch_news_map').select(
                'story_id'
            ).in_('topic_branch_id', branch_ids).execute()
            
            assigned_story_ids = {item['story_id'] for item in assigned_response.data} if assigned_response.data else set()
            print(f"  已分配新聞數: {len(assigned_story_ids)}")
            
            # 4. 找出未分配的新聞
            unassigned_story_ids = topic_story_ids - assigned_story_ids
            print(f"  ✓ 找到 {len(unassigned_story_ids)} 則未分配的新聞")
            
            if not unassigned_story_ids:
                return []
            
            # 5. 獲取新聞詳細內容
            return self._fetch_news_details(list(unassigned_story_ids))
            
        except Exception as e:
            print(f"✗ 獲取新新聞時發生錯誤: {e}")
            return []
    
    def _fetch_news_details(self, story_ids):
        """獲取新聞詳細內容"""
        if not story_ids:
            return []
        
        try:
            response = self.supabase.table('single_news').select(
                'story_id, news_title, long'
            ).in_('story_id', story_ids).execute()
            
            if response.data:
                news_items = []
                for news_data in response.data:
                    news_items.append({
                        'story_id': news_data.get('story_id'),
                        'news_title': news_data.get('news_title', ''),
                        'content': news_data.get('long', '')
                    })
                return news_items
            return []
        except Exception as e:
            print(f"✗ 獲取新聞詳細內容時發生錯誤: {e}")
            return []
    
    def fetch_existing_branches(self, topic_id):
        """
        獲取指定主題的所有現有分支資訊
        
        Args:
            topic_id: 主題ID
            
        Returns:
            分支列表，每個分支包含標題、內容和已有新聞
        """
        try:
            print(f"\n獲取主題 {topic_id} 的現有分支...")
            
            # 1. 獲取分支基本資訊
            branches_response = self.supabase.table('topic_branch').select(
                'topic_branch_id, topic_branch_title, topic_branch_content'
            ).eq('topic_id', topic_id).execute()
            
            if not branches_response.data:
                print(f"  主題 {topic_id} 沒有現有分支")
                return []
            
            branches = []
            for branch in branches_response.data:
                branch_id = branch['topic_branch_id']
                
                # 2. 獲取該分支的新聞
                news_map_response = self.supabase.table('topic_branch_news_map').select(
                    'story_id'
                ).eq('topic_branch_id', branch_id).execute()
                
                story_ids = [item['story_id'] for item in news_map_response.data] if news_map_response.data else []
                
                # 3. 獲取新聞詳細內容
                news_items = self._fetch_news_details(story_ids) if story_ids else []
                
                branches.append({
                    'topic_branch_id': branch_id,
                    'topic_branch_title': branch['topic_branch_title'],
                    'topic_branch_content': branch['topic_branch_content'],
                    'news_count': len(news_items),
                    'news_items': news_items
                })
                
                print(f"  分支: {branch['topic_branch_title']} ({len(news_items)} 則新聞)")
            
            print(f"✓ 共獲取 {len(branches)} 個分支")
            return branches
            
        except Exception as e:
            print(f"✗ 獲取現有分支時發生錯誤: {e}")
            return []
    
    def match_news_to_branch(self, new_news, existing_branches):
        """
        使用 AI 判斷新聞是否適合現有分支
        
        Args:
            new_news: 新新聞資訊 (dict)
            existing_branches: 現有分支列表
            
        Returns:
            (matched_branch_id, confidence_score) 或 (None, 0) 表示不匹配
        """
        if not self.genai_client or not existing_branches:
            return None, 0
        
        print(f"\n使用 AI 分析新聞: {new_news['news_title'][:30]}...")
        
        # 準備分支資訊
        branches_info = []
        for i, branch in enumerate(existing_branches):
            # 取前3則新聞作為代表，包含完整標題和內容摘要
            sample_news = branch['news_items'][:3]
            news_samples = []
            for news in sample_news:
                # 包含完整標題和內容前300字
                news_samples.append(
                    f"- 標題: {news['news_title']}\n"
                    f"  內容摘要: {news['content'][:300]}..."
                )
            
            branch_info = f"""
分支 {i+1}:
標題: {branch['topic_branch_title']}
描述: {branch['topic_branch_content']}
現有新聞數: {branch['news_count']}
範例新聞:
{chr(10).join(news_samples)}
"""
            branches_info.append(branch_info)
        
        # 準備新聞完整內容（根據內容長度決定是否截斷）
        news_content = new_news['content']
        # 如果內容超過 3000 字，取前 3000 字以避免 token 超限
        if len(news_content) > 3000:
            news_content = news_content[:3000] + "...\n(內容過長，已截取前 3000 字)"
            print(f"  ⚠️ 新聞內容過長 ({len(new_news['content'])} 字)，已截取前 3000 字進行分析")
        
        # 構建 prompt
        prompt = f"""
請判斷以下新聞是否適合加入現有的任一分支中。

**新聞資訊:**
標題: {new_news['news_title']}
完整內容: 
{news_content}

**現有分支:**
{chr(10).join(branches_info)}

請分析這則新聞的主題、內容和現有分支的相關性，然後以 JSON 格式回答:

{{
  "matched": true/false,
  "branch_index": 1-{len(existing_branches)} 或 null,
  "confidence": 0.0-1.0,
  "reason": "判斷理由（50字以內）"
}}

**判斷標準:**
1. 新聞主題與分支核心主題高度相關 (confidence > 0.7)
2. 新聞可以為該分支提供新的發展或角度 (confidence > 0.6)
3. 新聞與分支現有新聞有明確關聯 (confidence > 0.5)
4. 如果相關性較低 (confidence < 0.5)，設定 matched 為 false

只回傳 JSON，不要其他說明。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            result_text = response.text.strip()
            
            # 解析 JSON
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            
            matched = result.get('matched', False)
            branch_index = result.get('branch_index')
            confidence = result.get('confidence', 0.0)
            reason = result.get('reason', '')
            
            print(f"  AI 判斷: {'匹配' if matched else '不匹配'}")
            if matched and branch_index:
                branch = existing_branches[branch_index - 1]
                print(f"  匹配分支: {branch['topic_branch_title']}")
                print(f"  信心度: {confidence:.2f}")
                print(f"  理由: {reason}")
                return branch['topic_branch_id'], confidence
            else:
                print(f"  理由: {reason}")
                return None, confidence
                
        except Exception as e:
            print(f"  ✗ AI 分析時發生錯誤: {e}")
            return None, 0
    
    def get_or_create_other_branch(self, topic_id, test_mode=False):
        """
        獲取或創建「其他新聞」分支
        
        Args:
            topic_id: 主題ID
            test_mode: 測試模式，不實際寫入資料庫
            
        Returns:
            其他新聞分支的 ID
        """
        try:
            # 1. 檢查是否已有「其他新聞」分支
            response = self.supabase.table('topic_branch').select(
                'topic_branch_id'
            ).eq('topic_id', topic_id).eq('topic_branch_title', '其他相關新聞').execute()
            
            if response.data and len(response.data) > 0:
                branch_id = response.data[0]['topic_branch_id']
                print(f"  ✓ 找到現有「其他新聞」分支: {branch_id}")
                return branch_id
            
            # 2. 創建新的「其他新聞」分支
            new_branch_id = str(uuid.uuid4())
            
            if test_mode:
                print(f"  🧪 [測試] 將創建「其他新聞」分支: {new_branch_id}")
                return new_branch_id
            
            print(f"  創建新的「其他新聞」分支...")
            
            branch_data = {
                'topic_id': topic_id,
                'topic_branch_id': new_branch_id,
                'topic_branch_title': '其他相關新聞',
                'topic_branch_content': '包含與主題相關但不屬於其他特定分支的新聞'
            }
            
            insert_response = self.supabase.table('topic_branch').insert(branch_data).execute()
            
            if insert_response.data:
                print(f"  ✓ 成功創建「其他新聞」分支: {new_branch_id}")
                return new_branch_id
            else:
                print(f"  ✗ 創建「其他新聞」分支失敗")
                return None
                
        except Exception as e:
            print(f"✗ 獲取或創建「其他新聞」分支時發生錯誤: {e}")
            return None
    
    def assign_news_to_branch(self, story_id, branch_id, test_mode=False):
        """
        將新聞分配到指定分支
        
        Args:
            story_id: 新聞ID
            branch_id: 分支ID
            test_mode: 測試模式，不實際寫入資料庫
            
        Returns:
            是否成功
        """
        try:
            mapping_data = {
                'topic_branch_id': branch_id,
                'story_id': story_id
            }
            
            if test_mode:
                print(f"    🧪 [測試] 新聞 {story_id} 將分配到分支 {branch_id}")
                return True
            
            response = self.supabase.table('topic_branch_news_map').insert(mapping_data).execute()
            
            if response.data:
                print(f"    ✓ 新聞 {story_id} 已分配到分支 {branch_id}")
                return True
            else:
                print(f"    ✗ 新聞 {story_id} 分配失敗")
                return False
                
        except Exception as e:
            print(f"    ✗ 分配新聞時發生錯誤: {e}")
            return False
    
    def analyze_other_branch_for_new_clusters(self, topic_id, min_news_for_branch=3):
        """
        分析「其他新聞」分支，判斷是否可以組成新分支
        
        Args:
            topic_id: 主題ID
            min_news_for_branch: 組成新分支所需的最少新聞數 (預設 3)
            
        Returns:
            分析結果和建議
        """
        print("\n" + "=" * 60)
        print("🔍 分析「其他新聞」分支是否可組成新分支")
        print("=" * 60)
        
        try:
            # 1. 找到「其他新聞」分支
            response = self.supabase.table('topic_branch').select(
                'topic_branch_id, topic_branch_title'
            ).eq('topic_id', topic_id).eq('topic_branch_title', '其他相關新聞').execute()
            
            if not response.data:
                print("✓ 該主題沒有「其他新聞」分支")
                return None
            
            other_branch_id = response.data[0]['topic_branch_id']
            print(f"找到「其他新聞」分支: {other_branch_id}")
            
            # 2. 獲取該分支的所有新聞
            news_map_response = self.supabase.table('topic_branch_news_map').select(
                'story_id'
            ).eq('topic_branch_id', other_branch_id).execute()
            
            if not news_map_response.data:
                print("✓ 「其他新聞」分支目前沒有新聞")
                return None
            
            story_ids = [item['story_id'] for item in news_map_response.data]
            news_items = self._fetch_news_details(story_ids)
            
            print(f"「其他新聞」分支有 {len(news_items)} 則新聞")
            
            if len(news_items) < min_news_for_branch:
                print(f"✓ 新聞數少於 {min_news_for_branch} 則，暫不建議組成新分支")
                return None
            
            # 3. 使用 AI 分析是否可以組成新分支
            print("\n使用 AI 分析新聞群集...")
            
            # 準備新聞摘要
            news_summaries = []
            for i, news in enumerate(news_items, 1):
                news_summaries.append(
                    f"{i}. 【{news['news_title']}】\n"
                    f"   內容摘要: {news['content'][:250]}..."
                )
            
            prompt = f"""
請分析以下「其他新聞」分支中的 {len(news_items)} 則新聞，判斷是否可以組成新的主題分支。

新聞列表:
{chr(10).join(news_summaries)}

請分析:
1. 這些新聞中是否有多則新聞討論相同或相關的主題？
2. 是否有足夠的新聞（至少{min_news_for_branch}則）可以組成有意義的新分支？
3. 如果可以組成新分支，建議的分支標題和描述是什麼？哪些新聞應該歸入該分支？

以 JSON 格式回答:
{{
  "can_create_branch": true/false,
  "suggested_branches": [
    {{
      "branch_title": "建議的分支標題",
      "branch_description": "分支描述（100字內）",
      "news_indices": [1, 3, 5],  // 應該歸入此分支的新聞編號
      "reason": "為什麼這些新聞應該組成新分支（50字內）"
    }}
  ],
  "remaining_news_indices": [2, 4, 6]  // 仍應留在「其他新聞」的新聞編號
}}

注意:
- 如果無法組成有意義的新分支，設定 can_create_branch 為 false
- 可以建議多個新分支（如果新聞可以分成多個主題）
- 每個新分支至少要有 {min_news_for_branch} 則新聞
- 如果某些新聞無法組成新分支或與其他新聞主題不符，將其編號放入 remaining_news_indices
- remaining_news_indices 中的新聞將繼續保留在「其他新聞」分支

只回傳 JSON，不要其他說明。
"""
            
            try:
                response = self.genai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0
                    )
                )
                result_text = response.text.strip()
                
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3].strip()
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3].strip()
                
                result = json.loads(result_text)
                
                can_create = result.get('can_create_branch', False)
                
                if not can_create:
                    print("\n✓ AI 判斷: 目前的新聞無法組成有意義的新分支")
                    return None
                
                suggested_branches = result.get('suggested_branches', [])
                remaining_indices = result.get('remaining_news_indices', [])
                
                print(f"\n✅ AI 建議可以組成 {len(suggested_branches)} 個新分支:")
                
                for i, branch_suggestion in enumerate(suggested_branches, 1):
                    print(f"\n建議分支 {i}:")
                    print(f"  標題: {branch_suggestion['branch_title']}")
                    print(f"  描述: {branch_suggestion['branch_description']}")
                    print(f"  包含新聞數: {len(branch_suggestion['news_indices'])}")
                    print(f"  理由: {branch_suggestion['reason']}")
                
                if remaining_indices:
                    print(f"\n保留在「其他新聞」: {len(remaining_indices)} 則")
                else:
                    print(f"\n✓ 所有新聞都可組成新分支，「其他新聞」將清空")
                
                return {
                    'other_branch_id': other_branch_id,
                    'total_news': len(news_items),
                    'news_items': news_items,
                    'suggested_branches': suggested_branches,
                    'remaining_indices': remaining_indices
                }
                
            except Exception as e:
                print(f"✗ AI 分析失敗: {e}")
                return None
            
        except Exception as e:
            print(f"✗ 分析時發生錯誤: {e}")
            return None
    
    def create_branches_from_suggestions(self, topic_id, analysis_result):
        """
        根據分析建議創建新分支
        
        Args:
            topic_id: 主題ID
            analysis_result: analyze_other_branch_for_new_clusters 的返回結果
            
        Returns:
            創建結果統計
        """
        if not analysis_result or not analysis_result.get('suggested_branches'):
            print("沒有可執行的分支建議")
            return None
        
        print("\n" + "=" * 60)
        print("🔧 開始創建新分支")
        print("=" * 60)
        
        created_count = 0
        moved_count = 0
        
        other_branch_id = analysis_result['other_branch_id']
        news_items = analysis_result['news_items']
        suggested_branches = analysis_result['suggested_branches']
        
        try:
            for i, branch_suggestion in enumerate(suggested_branches, 1):
                print(f"\n[{i}/{len(suggested_branches)}] 創建分支: {branch_suggestion['branch_title']}")
                
                # 1. 創建新分支
                new_branch_id = str(uuid.uuid4())
                branch_data = {
                    'topic_id': topic_id,
                    'topic_branch_id': new_branch_id,
                    'topic_branch_title': branch_suggestion['branch_title'],
                    'topic_branch_content': branch_suggestion['branch_description']
                }
                
                insert_response = self.supabase.table('topic_branch').insert(branch_data).execute()
                
                if not insert_response.data:
                    print(f"  ✗ 創建分支失敗")
                    continue
                
                print(f"  ✓ 分支已創建: {new_branch_id}")
                created_count += 1
                
                # 2. 移動新聞到新分支
                news_indices = branch_suggestion['news_indices']
                story_ids_to_move = [news_items[idx - 1]['story_id'] for idx in news_indices if 0 < idx <= len(news_items)]
                
                moved = self.move_news_to_other_branch(story_ids_to_move, other_branch_id, new_branch_id)
                moved_count += moved
                print(f"  ✓ 已移動 {moved}/{len(story_ids_to_move)} 則新聞")
            
            print("\n" + "=" * 60)
            print("創建完成")
            print("=" * 60)
            print(f"成功創建: {created_count} 個新分支")
            print(f"總共移動: {moved_count} 則新聞")
            
            return {
                'created_branches': created_count,
                'moved_news': moved_count
            }
            
        except Exception as e:
            print(f"✗ 創建分支時發生錯誤: {e}")
            return None
    
    def process_topic_updates(self, topic_id, confidence_threshold=0.5, analyze_other_branch=True, test_mode=False):
        """
        處理指定主題的新聞更新
        
        Args:
            topic_id: 主題ID
            confidence_threshold: 匹配信心度閾值 (預設 0.5)
            analyze_other_branch: 處理完後是否分析「其他新聞」分支 (預設 True)
            test_mode: 測試模式，只預覽不寫入資料庫 (預設 False)
            
        Returns:
            處理結果統計
        """
        print("=" * 60)
        if test_mode:
            print(f"🧪 測試模式 - 處理主題 {topic_id} 的新聞更新（不寫入資料庫）")
        else:
            print(f"開始處理主題 {topic_id} 的新聞更新")
        print("=" * 60)
        
        # 1. 獲取新新聞
        new_news_list = self.fetch_new_news(topic_id)
        if not new_news_list:
            print("\n✓ 沒有需要處理的新新聞")
            return {
                'topic_id': topic_id,
                'new_news_count': 0,
                'matched_count': 0,
                'other_count': 0
            }
        
        print(f"\n找到 {len(new_news_list)} 則待處理的新聞")
        
        # 2. 獲取現有分支
        existing_branches = self.fetch_existing_branches(topic_id)
        
        # 3. 處理每則新聞
        matched_count = 0
        other_count = 0
        
        for i, news in enumerate(new_news_list, 1):
            print(f"\n[{i}/{len(new_news_list)}] 處理新聞: {news['news_title'][:40]}...")
            
            # 嘗試匹配現有分支
            matched_branch_id, confidence = self.match_news_to_branch(news, existing_branches)
            
            if matched_branch_id and confidence >= confidence_threshold:
                # 分配到匹配的分支
                if self.assign_news_to_branch(news['story_id'], matched_branch_id, test_mode):
                    matched_count += 1
            else:
                # 分配到「其他新聞」分支
                print(f"  新聞不適合現有分支，分配到「其他新聞」")
                other_branch_id = self.get_or_create_other_branch(topic_id, test_mode)
                if other_branch_id:
                    if self.assign_news_to_branch(news['story_id'], other_branch_id, test_mode):
                        other_count += 1
        
        # 4. 輸出統計
        print("\n" + "=" * 60)
        print("處理完成 - 統計資訊")
        print("=" * 60)
        print(f"待處理新聞: {len(new_news_list)}")
        print(f"匹配到現有分支: {matched_count}")
        print(f"分配到其他新聞: {other_count}")
        print(f"處理失敗: {len(new_news_list) - matched_count - other_count}")
        
        result = {
            'topic_id': topic_id,
            'new_news_count': len(new_news_list),
            'matched_count': matched_count,
            'other_count': other_count,
            'failed_count': len(new_news_list) - matched_count - other_count
        }
        
        # 5. 分析「其他新聞」分支是否可組成新分支
        if analyze_other_branch:
            print("\n" + "=" * 60)
            print("檢查「其他新聞」分支")
            print("=" * 60)
            
            # 測試模式下的特殊處理
            if test_mode and other_count > 0:
                print(f"🧪 [測試模式] 在實際執行時，會有 {other_count} 則新聞進入「其他新聞」分支")
                print("💡 建議：實際執行後可使用以下工具重新分析「其他新聞」分支：")
                print(f"   python other_news_regrouper.py process {topic_id}")
                print(f"   或使用 topic_group_update.py review {topic_id}")
            else:
                # 非測試模式或沒有新增到「其他新聞」的新聞
                analysis_result = self.analyze_other_branch_for_new_clusters(topic_id)
                
                if analysis_result:
                    print("\n是否要根據 AI 建議創建新分支？")
                    user_input = input("輸入 y 確認創建，其他鍵跳過: ").strip().lower()
                    
                    if user_input == 'y':
                        create_result = self.create_branches_from_suggestions(topic_id, analysis_result)
                        if create_result:
                            result['new_branches_created'] = create_result['created_branches']
                            result['news_reorganized'] = create_result['moved_news']
                    else:
                        print("✓ 已跳過創建新分支")
        
        return result
    
    def move_news_to_other_branch(self, story_ids, old_branch_id, new_branch_id):
        """
        將新聞從一個分支移動到另一個分支
        
        Args:
            story_ids: 要移動的新聞ID列表
            old_branch_id: 原分支ID
            new_branch_id: 目標分支ID
            
        Returns:
            成功移動的數量
        """
        success_count = 0
        
        for story_id in story_ids:
            try:
                # 1. 刪除舊的映射
                self.supabase.table('topic_branch_news_map').delete().eq(
                    'story_id', story_id
                ).eq('topic_branch_id', old_branch_id).execute()
                
                # 2. 創建新的映射
                mapping_data = {
                    'topic_branch_id': new_branch_id,
                    'story_id': story_id
                }
                response = self.supabase.table('topic_branch_news_map').insert(mapping_data).execute()
                
                if response.data:
                    success_count += 1
                    
            except Exception as e:
                print(f"      ✗ 移動新聞 {story_id} 時發生錯誤: {e}")
        
        return success_count
    
    def analyze_branch_quality(self, topic_id, auto_fix_low_cohesion=False, cohesion_threshold=0.5):
        """
        分析主題分支的品質，判斷是否需要重新分群
        
        Args:
            topic_id: 主題ID
            auto_fix_low_cohesion: 是否自動修復低內聚性分支（將新聞移到其他新聞分支）
            cohesion_threshold: 內聚性閾值，低於此值視為需要修復（預設 0.5）
            
        Returns:
            分析報告
        """
        print("=" * 60)
        print(f"分析主題 {topic_id} 的分支品質")
        if auto_fix_low_cohesion:
            print(f"⚙️ 自動修復模式已啟用（內聚性閾值: {cohesion_threshold}）")
        print("=" * 60)
        
        try:
            # 1. 獲取所有分支
            branches = self.fetch_existing_branches(topic_id)
            if not branches:
                print("\n該主題沒有任何分支")
                return None
            
            print(f"\n找到 {len(branches)} 個分支")
            
            # 2. 統計基本資訊
            total_news = sum(b['news_count'] for b in branches)
            avg_news_per_branch = total_news / len(branches) if branches else 0
            
            print(f"總新聞數: {total_news}")
            print(f"平均每分支新聞數: {avg_news_per_branch:.1f}")
            
            # 3. 使用 AI 分析每個分支的內聚性
            print("\n" + "=" * 60)
            print("使用 AI 分析各分支內聚性")
            print("=" * 60)
            
            branch_analysis = []
            
            for i, branch in enumerate(branches, 1):
                print(f"\n[{i}/{len(branches)}] 分析分支: {branch['topic_branch_title']}")
                print(f"  新聞數: {branch['news_count']}")
                
                if branch['news_count'] < 2:
                    print(f"  ⚠️ 新聞數過少，跳過內聚性分析")
                    branch_analysis.append({
                        'branch': branch,
                        'cohesion_score': 0.5,
                        'suggestion': '新聞數過少',
                        'details': '建議考慮合併到其他相關分支'
                    })
                    continue
                
                cohesion_result = self._analyze_branch_cohesion(branch)
                branch_analysis.append({
                    'branch': branch,
                    'cohesion_score': cohesion_result['score'],
                    'suggestion': cohesion_result['suggestion'],
                    'details': cohesion_result['details']
                })
                
                print(f"  內聚性評分: {cohesion_result['score']:.2f}/1.0")
                print(f"  建議: {cohesion_result['suggestion']}")
            
            # 3.5. 如果啟用自動修復，處理低內聚性分支
            if auto_fix_low_cohesion:
                print("\n" + "=" * 60)
                print("🔧 自動修復低內聚性分支")
                print("=" * 60)
                
                # 獲取或創建「其他新聞」分支
                other_branch_id = self.get_or_create_other_branch(topic_id)
                
                if not other_branch_id:
                    print("✗ 無法獲取或創建「其他新聞」分支，跳過自動修復")
                else:
                    moved_total = 0
                    for analysis in branch_analysis:
                        branch = analysis['branch']
                        cohesion_score = analysis['cohesion_score']
                        
                        # 跳過「其他新聞」分支本身
                        if branch['topic_branch_title'] == '其他相關新聞':
                            continue
                        
                        # 如果內聚性過低，移動新聞
                        if cohesion_score < cohesion_threshold and branch['news_count'] > 0:
                            print(f"\n處理分支: {branch['topic_branch_title']}")
                            print(f"  內聚性: {cohesion_score:.2f} < {cohesion_threshold}")
                            print(f"  準備移動 {branch['news_count']} 則新聞到「其他新聞」分支...")
                            
                            story_ids = [news['story_id'] for news in branch['news_items']]
                            moved_count = self.move_news_to_other_branch(
                                story_ids, 
                                branch['topic_branch_id'], 
                                other_branch_id
                            )
                            
                            if moved_count > 0:
                                print(f"  ✓ 成功移動 {moved_count}/{branch['news_count']} 則新聞")
                                moved_total += moved_count
                                
                                # 更新分析結果
                                analysis['moved_to_other'] = True
                                analysis['moved_count'] = moved_count
                            else:
                                print(f"  ✗ 移動失敗")
                    
                    if moved_total > 0:
                        print(f"\n✅ 總計移動了 {moved_total} 則新聞到「其他新聞」分支")
                    else:
                        print(f"\n✓ 沒有需要移動的新聞")
            
            # 5. 生成總體建議
            print("\n" + "=" * 60)
            print("分析報告與建議")
            print("=" * 60)
            
            needs_regrouping = False
            reasons = []
            
            # 檢查內聚性問題
            low_cohesion_branches = [a for a in branch_analysis if a['cohesion_score'] < 0.6]
            if low_cohesion_branches:
                needs_regrouping = True
                reasons.append(f"發現 {len(low_cohesion_branches)} 個內聚性較低的分支")
            
            # 檢查分支數量
            if len(branches) == 1 and total_news > 5:
                needs_regrouping = True
                reasons.append(f"只有1個分支但有{total_news}則新聞，可能過於籠統")
            
            if len(branches) > total_news * 0.5:
                needs_regrouping = True
                reasons.append(f"分支數({len(branches)})過多，可能過度細分")
            
            # 檢查不平衡問題
            if branches:
                max_news = max(b['news_count'] for b in branches)
                min_news = min(b['news_count'] for b in branches)
                if max_news > min_news * 5 and len(branches) > 2:
                    reasons.append(f"分支新聞數嚴重不平衡 (最多{max_news}則 vs 最少{min_news}則)")
            
            # 輸出報告
            print(f"\n{'⚠️  建議重新分群' if needs_regrouping else '✅ 分支結構良好'}")
            
            if needs_regrouping:
                print("\n理由:")
                for reason in reasons:
                    print(f"  • {reason}")
            
            print("\n詳細分析:")
            for i, analysis in enumerate(branch_analysis, 1):
                branch = analysis['branch']
                print(f"\n{i}. {branch['topic_branch_title']}")
                print(f"   新聞數: {branch['news_count']}")
                print(f"   內聚性: {analysis['cohesion_score']:.2f}")
                print(f"   評價: {analysis['suggestion']}")
                if analysis['details']:
                    print(f"   詳情: {analysis['details']}")
            
            return {
                'topic_id': topic_id,
                'needs_regrouping': needs_regrouping,
                'reasons': reasons,
                'branches_count': len(branches),
                'total_news': total_news,
                'branch_analysis': branch_analysis
            }
            
        except Exception as e:
            print(f"✗ 分析時發生錯誤: {e}")
            return None
    
    def _analyze_branch_cohesion(self, branch):
        """使用 AI 分析單一分支的內聚性"""
        if not self.genai_client or branch['news_count'] < 2:
            return {'score': 0.5, 'suggestion': '無法分析', 'details': ''}
        
        # 準備新聞摘要
        news_summaries = []
        for i, news in enumerate(branch['news_items'][:5], 1):  # 最多取5則
            news_summaries.append(
                f"{i}. {news['news_title']}\n"
                f"   內容: {news['content'][:200]}..."
            )
        
        prompt = f"""
請分析以下分支的內聚性（新聞之間的主題相關性）。

分支標題: {branch['topic_branch_title']}
分支描述: {branch['topic_branch_content']}
新聞數: {branch['news_count']}

範例新聞:
{chr(10).join(news_summaries)}

請評估:
1. 這些新聞是否圍繞同一個核心主題？
2. 新聞之間的關聯性強度如何？
3. 是否有新聞明顯偏離主題？

以 JSON 格式回答:
{{
  "cohesion_score": 0.0-1.0,
  "suggestion": "優秀/良好/普通/需改善",
  "details": "簡短說明（50字內）"
}}

評分標準:
- 0.8-1.0: 主題高度一致，所有新聞緊密相關
- 0.6-0.8: 主題基本一致，大部分新聞相關
- 0.4-0.6: 主題較分散，部分新聞關聯性弱
- 0.0-0.4: 主題混亂，新聞之間缺乏明確關聯

只回傳 JSON，不要其他說明。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            result_text = response.text.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            return {
                'score': result.get('cohesion_score', 0.5),
                'suggestion': result.get('suggestion', '無法判斷'),
                'details': result.get('details', '')
            }
        except Exception as e:
            print(f"    ✗ AI 分析失敗: {e}")
            return {'score': 0.5, 'suggestion': '分析失敗', 'details': str(e)}
    
    def _analyze_branch_overlap(self, branches):
        """分析分支間是否有主題重疊"""
        if not self.genai_client or len(branches) < 2:
            return []
        
        issues = []
        
        # 比較每對分支
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                branch_a = branches[i]
                branch_b = branches[j]
                
                prompt = f"""
請判斷以下兩個分支是否有主題重疊或過於相似。

分支 A:
標題: {branch_a['topic_branch_title']}
描述: {branch_a['topic_branch_content']}

分支 B:
標題: {branch_b['topic_branch_title']}
描述: {branch_b['topic_branch_content']}

以 JSON 格式回答:
{{
  "has_overlap": true/false,
  "severity": "high/medium/low",
  "reason": "簡短說明（30字內）"
}}

只回傳 JSON，不要其他說明。
"""
                
                try:
                    response = self.genai_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                    temperature=0.0
                )
                    )
                    result_text = response.text.strip()
                    
                    if result_text.startswith('```json'):
                        result_text = result_text[7:-3].strip()
                    elif result_text.startswith('```'):
                        result_text = result_text[3:-3].strip()
                    
                    result = json.loads(result_text)
                    
                    if result.get('has_overlap'):
                        severity = result.get('severity', 'low')
                        reason = result.get('reason', '')
                        issues.append(
                            f"「{branch_a['topic_branch_title']}」與「{branch_b['topic_branch_title']}」"
                            f"有{severity}度重疊 - {reason}"
                        )
                except Exception:
                    continue
        
        return issues
    
    def process_all_topics(self, confidence_threshold=0.5):
        """
        處理所有主題的新聞更新
        
        Args:
            confidence_threshold: 匹配信心度閾值
            
        Returns:
            所有主題的處理結果
        """
        print("=" * 60)
        print("開始處理所有主題的新聞更新")
        print("=" * 60)
        
        try:
            # 獲取所有主題
            response = self.supabase.table('topic_branch').select('topic_id').execute()
            
            if not response.data:
                print("沒有找到任何主題")
                return []
            
            topic_ids = list(set(item['topic_id'] for item in response.data))
            print(f"\n找到 {len(topic_ids)} 個主題")
            
            results = []
            for topic_id in topic_ids:
                result = self.process_topic_updates(topic_id, confidence_threshold)
                results.append(result)
                print()
            
            # 總計統計
            print("\n" + "=" * 60)
            print("全部處理完成 - 總計統計")
            print("=" * 60)
            total_new = sum(r['new_news_count'] for r in results)
            total_matched = sum(r['matched_count'] for r in results)
            total_other = sum(r['other_count'] for r in results)
            total_failed = sum(r['failed_count'] for r in results)
            
            print(f"處理主題數: {len(results)}")
            print(f"總新聞數: {total_new}")
            print(f"匹配到現有分支: {total_matched}")
            print(f"分配到其他新聞: {total_other}")
            print(f"處理失敗: {total_failed}")
            
            return results
            
        except Exception as e:
            print(f"✗ 處理所有主題時發生錯誤: {e}")
            return []


def test_fetch_new_news(updater, topic_id):
    """測試：獲取新新聞"""
    print("\n" + "=" * 60)
    print("測試 1: 獲取新新聞")
    print("=" * 60)
    
    new_news = updater.fetch_new_news(topic_id)
    if new_news:
        print(f"\n✓ 找到 {len(new_news)} 則未分配的新聞:")
        for i, news in enumerate(new_news[:5], 1):  # 只顯示前5則
            print(f"\n{i}. story_id: {news['story_id']}")
            print(f"   標題: {news['news_title'][:60]}...")
            print(f"   內容長度: {len(news['content'])} 字")
        if len(new_news) > 5:
            print(f"\n... 還有 {len(new_news) - 5} 則新聞")
    else:
        print("\n✓ 沒有未分配的新聞")
    
    return new_news


def test_fetch_branches(updater, topic_id):
    """測試：獲取現有分支"""
    print("\n" + "=" * 60)
    print("測試 2: 獲取現有分支")
    print("=" * 60)
    
    branches = updater.fetch_existing_branches(topic_id)
    if branches:
        print(f"\n✓ 找到 {len(branches)} 個分支:")
        for i, branch in enumerate(branches, 1):
            print(f"\n{i}. {branch['topic_branch_title']}")
            print(f"   分支 ID: {branch['topic_branch_id']}")
            print(f"   描述: {branch['topic_branch_content'][:80]}...")
            print(f"   新聞數: {branch['news_count']}")
    else:
        print("\n✓ 沒有現有分支")
    
    return branches


def test_match_single_news(updater, new_news, branches):
    """測試：匹配單則新聞"""
    print("\n" + "=" * 60)
    print("測試 3: AI 匹配測試（單則新聞）")
    print("=" * 60)
    
    if not new_news:
        print("\n⚠️ 沒有新聞可測試")
        return
    
    if not branches:
        print("\n⚠️ 沒有分支可匹配")
        return
    
    # 測試第一則新聞
    test_news = new_news[0]
    print(f"\n測試新聞:")
    print(f"標題: {test_news['news_title']}")
    print(f"內容長度: {len(test_news['content'])} 字")
    print(f"內容預覽: {test_news['content'][:150]}...")
    
    matched_branch_id, confidence = updater.match_news_to_branch(test_news, branches)
    
    if matched_branch_id:
        matched_branch = next((b for b in branches if b['topic_branch_id'] == matched_branch_id), None)
        if matched_branch:
            print(f"\n✓ 匹配成功！")
            print(f"  匹配分支: {matched_branch['topic_branch_title']}")
            print(f"  信心度: {confidence:.2%}")
    else:
        print(f"\n✓ 無匹配分支（信心度: {confidence:.2%}）")
        print(f"  → 將分配到「其他新聞」分支")


def review_and_analyze_mode(updater, topic_id=None, auto_fix=False):
    """檢視分支並分析是否需要重新分群"""
    print("\n🔍 檢視分支與分群分析模式")
    print("=" * 60)
    
    if not topic_id:
        topic_id = input("\n請輸入要檢視的主題 ID: ").strip()
    
    if not topic_id:
        print("❌ 無效的主題 ID")
        return
    
    # 1. 獲取並顯示現有分支
    branches = test_fetch_branches(updater, topic_id)
    
    if not branches:
        print("\n⚠️ 該主題沒有任何分支")
        return
    
    # 2. 詢問是否啟用自動修復
    if not auto_fix:
        print("\n是否要自動修復低內聚性分支？")
        print("（將內聚性過低的分支中的新聞移動到「其他新聞」分支）")
        auto_fix_input = input("輸入 y 啟用，其他鍵跳過: ").strip().lower()
        auto_fix = (auto_fix_input == 'y')
    
    # 3. 執行深度分析
    print("\n正在進行深度分析...")
    analysis_result = updater.analyze_branch_quality(
        topic_id, 
        auto_fix_low_cohesion=auto_fix,
        cohesion_threshold=0.5
    )
    
    if not analysis_result:
        print("\n❌ 分析失敗")
        return
    
    # 4. 詢問是否需要進一步操作
    if analysis_result['needs_regrouping']:
        print("\n" + "=" * 60)
        print("💡 後續操作建議")
        print("=" * 60)
        print("由於發現分支品質問題，您可以:")
        print("1. 使用原始的分群工具重新對該主題進行分群")
        print("2. 手動調整問題分支")
        print("3. 繼續使用目前的分支結構")
    
    return analysis_result


def test_mode_interactive(updater, topic_id=None):
    """測試模式：只查看不寫入"""
    print("\n🧪 進入測試模式 (只查看，不寫入資料庫)")
    print("=" * 60)
    
    if not topic_id:
        topic_id = input("\n請輸入要測試的主題 ID: ").strip()
    
    if not topic_id:
        print("❌ 無效的主題 ID")
        return
    
    # 測試 1: 獲取新新聞
    new_news = test_fetch_new_news(updater, topic_id)
    
    # 測試 2: 獲取現有分支
    branches = test_fetch_branches(updater, topic_id)
    
    # 測試 3: 測試匹配
    if new_news and branches:
        test_match_single_news(updater, new_news, branches)
    
    # 測試總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"主題 ID: {topic_id}")
    print(f"未分配新聞: {len(new_news)} 則")
    print(f"現有分支: {len(branches)} 個")
    
    if new_news and branches:
        print("\n✅ 測試完成！資料結構正常，可以執行正式處理。")
    elif not new_news:
        print("\n⚠️ 沒有未分配的新聞，無需處理。")
    elif not branches:
        print("\n⚠️ 沒有現有分支，所有新聞將進入「其他新聞」分支。")


def main():
    """主程式入口"""
    print("🚀 新聞分支更新器 - 啟動中...")
    print("📋 功能: 自動將新新聞分配到合適的分支")
    print("=" * 60)
    
    # 檢查命令列參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test' or command == '--test' or command == '-t':
            # 測試模式
            try:
                updater = NewsBranchUpdater()
                topic_id = sys.argv[2] if len(sys.argv) > 2 else None
                test_mode_interactive(updater, topic_id)
            except Exception as e:
                print(f"❌ 測試失敗: {e}")
            return
        
        elif command == 'review' or command == '--review' or command == '-r':
            # 檢視分析模式
            try:
                updater = NewsBranchUpdater()
                topic_id = sys.argv[2] if len(sys.argv) > 2 else None
                # 檢查是否有 --fix 參數
                auto_fix = '--fix' in sys.argv or '-f' in sys.argv
                review_and_analyze_mode(updater, topic_id, auto_fix)
            except Exception as e:
                print(f"❌ 分析失敗: {e}")
            return
        
        elif command == 'process' or command == '--process' or command == '-p':
            # 處理單一專題模式
            try:
                updater = NewsBranchUpdater()
                topic_id = sys.argv[2] if len(sys.argv) > 2 else None
                
                if not topic_id:
                    print("❌ 請提供專題 ID")
                    print("使用方式: python topic_group_update.py process <topic_id>")
                    return
                
                # 檢查是否有 test 參數
                test_mode = 'test' in sys.argv or '--test' in sys.argv or '-t' in sys.argv
                
                updater.process_topic_updates(topic_id, test_mode=test_mode)
            except Exception as e:
                print(f"❌ 處理失敗: {e}")
            return
        
        elif command == 'help' or command == '--help' or command == '-h':
            # 顯示幫助
            print("\n使用方式:")
            print("  python topic_group_update.py                            # 互動模式")
            print("  python topic_group_update.py test [topic_id]            # 測試模式（查看分支和新聞）")
            print("  python topic_group_update.py process <topic_id>         # 處理單一專題（寫入資料庫）")
            print("  python topic_group_update.py process <topic_id> test    # 處理單一專題（測試模式，不寫入）")
            print("  python topic_group_update.py review [topic_id]          # 檢視分支分析模式")
            print("  python topic_group_update.py review [topic_id] --fix    # 檢視並自動修復低內聚性分支")
            print("  python topic_group_update.py --help                     # 顯示此幫助")
            print("\n範例:")
            print("  python topic_group_update.py test 12345                 # 測試主題 12345")
            print("  python topic_group_update.py process 12345              # 處理主題 12345 的新新聞")
            print("  python topic_group_update.py process 12345 test         # 處理主題 12345（測試模式）")
            print("  python topic_group_update.py review 12345               # 檢視並分析主題 12345")
            print("  python topic_group_update.py review 12345 --fix         # 檢視並自動修復主題 12345")
            print("  python topic_group_update.py review                     # 檢視模式（會提示輸入主題ID）")
            return
    
    # 互動模式
    try:
        updater = NewsBranchUpdater()
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return
    
    print("\n請選擇處理模式:")
    print("1. 處理單一主題（新增新聞到分支）")
    print("2. 處理所有主題（批次處理）")
    print("3. 測試模式（只查看不寫入）")
    print("4. 檢視分支並分析分群品質")
    
    try:
        choice = input("\n請輸入選項 (1/2/3/4): ").strip()
        
        if choice == '1':
            topic_id = input("請輸入主題 ID: ").strip()
            if topic_id:
                updater.process_topic_updates(topic_id)
            else:
                print("❌ 無效的主題 ID")
        elif choice == '2':
            updater.process_all_topics()
        elif choice == '3':
            test_mode_interactive(updater)
        elif choice == '4':
            review_and_analyze_mode(updater)
        else:
            print("❌ 無效的選項")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷程式執行")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
    
    print("\n程式結束")


if __name__ == "__main__":
    main()
