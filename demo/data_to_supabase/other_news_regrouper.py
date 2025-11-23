"""
「其他新聞」分支重新分群工具
遍歷所有主題的「其他新聞」分支，使用 AI 進行智能分群
參考 complete_news_grouper.py 的分群邏輯
"""

import os
import sys
import json
import uuid
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


class OtherNewsRegrouper:
    """「其他新聞」分支重新分群工具"""
    
    def __init__(self):
        """初始化客戶端"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            print("✓ Gemini Client 初始化成功")
        except Exception as e:
            print(f"✗ Gemini Client 初始化失敗: {e}")
            self.genai_client = None
    
    def get_all_topics_with_other_branch(self):
        """
        獲取所有擁有「其他新聞」分支的主題
        
        Returns:
            主題列表，每個主題包含 topic_id 和 other_branch_id
        """
        try:
            print("正在查詢所有擁有「其他新聞」分支的主題...")
            
            response = self.supabase.table('topic_branch').select(
                'topic_id, topic_branch_id'
            ).eq('topic_branch_title', '其他相關新聞').execute()
            
            if not response.data:
                print("✓ 沒有找到任何「其他新聞」分支")
                return []
            
            topics = []
            for item in response.data:
                topics.append({
                    'topic_id': item['topic_id'],
                    'other_branch_id': item['topic_branch_id']
                })
            
            print(f"✓ 找到 {len(topics)} 個擁有「其他新聞」分支的主題")
            return topics
            
        except Exception as e:
            print(f"✗ 查詢時發生錯誤: {e}")
            return []
    
    def get_other_branch_news(self, other_branch_id):
        """
        獲取「其他新聞」分支的所有新聞
        
        Args:
            other_branch_id: 「其他新聞」分支ID
            
        Returns:
            新聞列表
        """
        try:
            # 1. 獲取該分支的所有新聞 ID
            news_map_response = self.supabase.table('topic_branch_news_map').select(
                'story_id'
            ).eq('topic_branch_id', other_branch_id).execute()
            
            if not news_map_response.data:
                return []
            
            story_ids = [item['story_id'] for item in news_map_response.data]
            
            # 2. 獲取新聞詳細內容
            response = self.supabase.table('single_news').select(
                'story_id, news_title, long'
            ).in_('story_id', story_ids).execute()
            
            if not response.data:
                return []
            
            news_items = []
            for news_data in response.data:
                news_items.append({
                    'story_id': news_data.get('story_id'),
                    'news_title': news_data.get('news_title', ''),
                    'content': news_data.get('long', '')
                })
            
            return news_items
            
        except Exception as e:
            print(f"  ✗ 獲取新聞時發生錯誤: {e}")
            return []
    
    def group_news_by_events_ai(self, news_items, min_news_per_group=3):
        """
        使用 Gemini AI 將「其他新聞」分組為事件分支
        參考 complete_news_grouper.py 的分群邏輯
        
        Args:
            news_items: 新聞列表
            min_news_per_group: 每組最少新聞數
            
        Returns:
            分組結果列表
        """
        if not self.genai_client or not news_items:
            return []
        
        print(f"  使用 AI 分析 {len(news_items)} 則新聞...")
        
        # 準備新聞摘要資料供模型分析
        news_summaries = []
        for i, news in enumerate(news_items):
            title = news['news_title'][:100]
            content = news['content'][:300]
            summary = f"新聞{i+1}：標題：{title}；內容：{content}..."
            news_summaries.append(summary)
        
        # 構建提示語（參考 complete_news_grouper.py）
        prompt = f"""
請分析以下「其他新聞」分支中的 {len(news_items)} 則新聞，將它們按照**核心事件主題**進行分組。

**分組準則：**
1. **共同主題或核心事件**：新聞內容圍繞同一核心事件或議題展開，才能歸為一組。
2. **內容相關性**：同一組內的新聞應探討事件的不同面向、發展階段或關鍵細節。
3. **避免過度細分**：除非新聞內容明顯不同，否則應該合併到同一個分組。優先考慮合併相關事件。
4. **合理組規模**：每組建議包含至少 {min_news_per_group} 則新聞，避免創建太多小分組。
5. **單一歸屬**：每則新聞只能屬於一個分組。
6. **可以有未分配新聞**：如果某些新聞與其他新聞主題不符，可以不分配（留在原「其他新聞」分支）。
7. **不要創建「其他」分組**：不要創建「其他」、「其他相關新聞」、「未分類」等籠統分組。

新聞資料：
{chr(10).join(news_summaries)}

請嚴格按照以下 JSON 格式輸出分組結果：
{{
  "groups": [
    {{
      "event_title": "**具體事件標題 (10字以內)**",
      "event_summary": "簡潔說明該事件核心內容 (80字以內)",
      "news_indices": [1, 2, 3, 4, 5],
      "reason": "為什麼這些新聞應該組成新分支（50字以內）"
    }},
    {{
      "event_title": "**另一個事件標題 (10字以內)**",
      "event_summary": "另一個事件的說明",
      "news_indices": [6, 7, 8],
      "reason": "理由說明"
    }}
  ]
}}

**評估標準：**
* **避免過度細分**：優先將相關事件合併，不要為了細分而細分。
* **分組的實用性**：每個分組應該有足夠的新聞數量（至少 {min_news_per_group} 則）。
* **標題的代表性**：分組標題應該能涵蓋該組大部分新聞的主題。
* **允許未分配**：無法組成有意義分組的新聞可以不分配。

**輸出要求：**
* **僅回傳 JSON 格式的輸出**，不包含任何額外的解釋文字。
* `event_title` 必須為**具體且精煉**的標題，長度控制在 10 字以內。
* `news_indices` 為新聞列表中的編號，從 1 開始。
* **如果無法組成有意義的分組，可以返回空的 groups 陣列**。
* **絕對不要創建「其他」或「未分類」的分組**。
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
            
            # 解析 JSON 結果
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            groups = result.get('groups', [])
            
            if not groups:
                print("  ✓ AI 判斷: 無法組成有意義的新分支")
                return []
            
            print(f"  ✓ AI 分析完成，共分為 {len(groups)} 個潛在新分支")
            
            # 轉換為標準格式，並確保每個分組至少有最少新聞數
            # 同時確保每則新聞只出現在一個分組中
            event_groups = []
            used_news_indices = set()
            
            for group in groups:
                event_title = group.get('event_title', '未命名事件')
                event_summary = group.get('event_summary', '')
                news_indices = group.get('news_indices', [])
                reason = group.get('reason', '相關新聞群集')
                
                # 過濾掉已使用的新聞索引
                valid_indices = [idx for idx in news_indices 
                                if 1 <= idx <= len(news_items) and idx not in used_news_indices]
                
                # 過濾掉不符合最少新聞數要求的分組
                if len(valid_indices) >= min_news_per_group:
                    # 標記這些索引為已使用
                    used_news_indices.update(valid_indices)
                    
                    # 獲取對應的新聞項目
                    group_news = [news_items[idx - 1] for idx in valid_indices]
                    
                    event_groups.append({
                        'event_id': str(uuid.uuid4()),
                        'event_title': event_title,
                        'event_summary': event_summary,
                        'news_count': len(group_news),
                        'news_items': group_news,
                        'news_indices': valid_indices,
                        'reason': reason
                    })
                    print(f"    ✓ 分支「{event_title}」: {len(valid_indices)} 則新聞")
                else:
                    if len(valid_indices) > 0:
                        print(f"    ⚠️ 跳過分支「{event_title}」: 新聞數 {len(valid_indices)} < {min_news_per_group}")
            
            return event_groups
            
        except Exception as e:
            print(f"  ✗ AI 分析時發生錯誤: {e}")
            return []
    
    def create_new_branches_and_move_news(self, topic_id, other_branch_id, event_groups, test_mode=False):
        """
        創建新分支並移動新聞
        
        Args:
            topic_id: 主題ID
            other_branch_id: 「其他新聞」分支ID
            event_groups: AI 分析的分組結果
            test_mode: 測試模式，不實際寫入資料庫
            
        Returns:
            創建結果統計
        """
        if not event_groups:
            return {'created_branches': 0, 'moved_news': 0}
        
        created_count = 0
        moved_count = 0
        
        print(f"\n  {'🧪 [測試模式] ' if test_mode else ''}開始創建新分支...")
        
        try:
            for i, group in enumerate(event_groups, 1):
                new_branch_id = group['event_id']
                branch_title = group['event_title']
                branch_content = group['event_summary']
                
                if test_mode:
                    print(f"    [{i}/{len(event_groups)}] 🧪 將創建分支: {branch_title}")
                    print(f"        分支 ID: {new_branch_id}")
                    print(f"        將移動 {group['news_count']} 則新聞")
                    created_count += 1
                    moved_count += group['news_count']
                else:
                    print(f"    [{i}/{len(event_groups)}] 創建分支: {branch_title}")
                    
                    # 1. 創建新分支
                    branch_data = {
                        'topic_id': topic_id,
                        'topic_branch_id': new_branch_id,
                        'topic_branch_title': branch_title,
                        'topic_branch_content': branch_content
                    }
                    
                    insert_response = self.supabase.table('topic_branch').insert(branch_data).execute()
                    
                    if not insert_response.data:
                        print("        ✗ 創建分支失敗")
                        continue
                    
                    print(f"        ✓ 分支已創建: {new_branch_id}")
                    created_count += 1
                    
                    # 2. 移動新聞到新分支
                    story_ids = [news['story_id'] for news in group['news_items']]
                    moved = self._move_news_between_branches(story_ids, other_branch_id, new_branch_id)
                    moved_count += moved
                    print(f"        ✓ 已移動 {moved}/{len(story_ids)} 則新聞")
            
            return {
                'created_branches': created_count,
                'moved_news': moved_count
            }
            
        except Exception as e:
            print(f"  ✗ 創建分支時發生錯誤: {e}")
            return {'created_branches': created_count, 'moved_news': moved_count}
    
    def _move_news_between_branches(self, story_ids, old_branch_id, new_branch_id):
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
                print(f"          ✗ 移動新聞 {story_id} 時發生錯誤: {e}")
        
        return success_count
    
    def process_single_topic(self, topic_id, min_news_for_branch=3, test_mode=False):
        """
        處理單一主題的「其他新聞」分支
        
        Args:
            topic_id: 主題ID
            min_news_for_branch: 組成新分支所需的最少新聞數
            test_mode: 測試模式，不實際寫入資料庫
            
        Returns:
            處理結果
        """
        print(f"\n{'='*60}")
        print(f"{'🧪 [測試模式] ' if test_mode else ''}處理主題: {topic_id}")
        print(f"{'='*60}")
        
        try:
            # 1. 找到「其他新聞」分支
            response = self.supabase.table('topic_branch').select(
                'topic_branch_id'
            ).eq('topic_id', topic_id).eq('topic_branch_title', '其他相關新聞').execute()
            
            if not response.data:
                print("✓ 該主題沒有「其他新聞」分支")
                return None
            
            other_branch_id = response.data[0]['topic_branch_id']
            print(f"✓ 找到「其他新聞」分支: {other_branch_id}")
            
            # 2. 獲取該分支的所有新聞
            news_items = self.get_other_branch_news(other_branch_id)
            
            if not news_items:
                print("✓ 「其他新聞」分支目前沒有新聞")
                return None
            
            print(f"✓ 「其他新聞」分支有 {len(news_items)} 則新聞")
            
            if len(news_items) < min_news_for_branch:
                print(f"✓ 新聞數少於 {min_news_for_branch} 則，暫不進行重新分群")
                return None
            
            # 3. 使用 AI 進行分群
            event_groups = self.group_news_by_events_ai(news_items, min_news_for_branch)
            
            if not event_groups:
                print("✓ 無法組成有意義的新分支")
                return None
            
            # 4. 計算剩餘新聞
            all_indices = set(range(1, len(news_items) + 1))
            used_indices = set()
            for group in event_groups:
                used_indices.update(group['news_indices'])
            
            remaining_count = len(all_indices - used_indices)
            
            print(f"\n{'='*60}")
            print("分群結果")
            print(f"{'='*60}")
            print(f"可組成新分支數: {len(event_groups)}")
            print(f"將移動新聞數: {sum(g['news_count'] for g in event_groups)}")
            print(f"保留在「其他新聞」: {remaining_count} 則")
            
            for i, group in enumerate(event_groups, 1):
                print(f"\n建議分支 {i}:")
                print(f"  標題: {group['event_title']}")
                print(f"  描述: {group['event_summary']}")
                print(f"  包含新聞數: {group['news_count']}")
                print(f"  理由: {group['reason']}")
            
            # 5. 詢問是否創建新分支（非測試模式）
            if not test_mode:
                print(f"\n{'='*60}")
                user_input = input("是否要根據 AI 建議創建新分支？(y/n): ").strip().lower()
                
                if user_input != 'y':
                    print("✓ 已跳過創建新分支")
                    return None
            
            # 6. 創建新分支並移動新聞
            result = self.create_new_branches_and_move_news(
                topic_id, 
                other_branch_id, 
                event_groups, 
                test_mode
            )
            
            print(f"\n{'='*60}")
            print("處理完成")
            print(f"{'='*60}")
            print(f"成功創建: {result['created_branches']} 個新分支")
            print(f"總共移動: {result['moved_news']} 則新聞")
            print(f"保留在「其他新聞」: {remaining_count} 則新聞")
            
            return {
                'topic_id': topic_id,
                'original_news_count': len(news_items),
                'created_branches': result['created_branches'],
                'moved_news': result['moved_news'],
                'remaining_news': remaining_count
            }
            
        except Exception as e:
            print(f"✗ 處理時發生錯誤: {e}")
            return None
    
    def process_all_topics(self, min_news_for_branch=3, test_mode=False, auto_confirm=False):
        """
        處理所有主題的「其他新聞」分支
        
        Args:
            min_news_for_branch: 組成新分支所需的最少新聞數
            test_mode: 測試模式，不實際寫入資料庫
            auto_confirm: 自動確認所有操作，不詢問使用者
            
        Returns:
            所有主題的處理結果
        """
        print("=" * 60)
        print(f"{'🧪 [測試模式] ' if test_mode else ''}開始處理所有主題的「其他新聞」分支")
        print("=" * 60)
        
        # 1. 獲取所有擁有「其他新聞」分支的主題
        topics = self.get_all_topics_with_other_branch()
        
        if not topics:
            print("\n✓ 沒有需要處理的主題")
            return []
        
        # 2. 處理每個主題
        results = []
        
        for i, topic_info in enumerate(topics, 1):
            topic_id = topic_info['topic_id']
            other_branch_id = topic_info['other_branch_id']
            
            print(f"\n[{i}/{len(topics)}] 處理主題 {topic_id}...")
            
            # 獲取該分支的新聞數量
            news_items = self.get_other_branch_news(other_branch_id)
            
            if not news_items:
                print("  ✓ 該分支沒有新聞，跳過")
                continue
            
            print(f"  ✓ 該分支有 {len(news_items)} 則新聞")
            
            if len(news_items) < min_news_for_branch:
                print(f"  ✓ 新聞數少於 {min_news_for_branch} 則，跳過")
                continue
            
            # 分析分群
            event_groups = self.group_news_by_events_ai(news_items, min_news_for_branch)
            
            if not event_groups:
                print("  ✓ 無法組成有意義的新分支，跳過")
                continue
            
            # 顯示分群結果
            print(f"\n  可組成 {len(event_groups)} 個新分支:")
            for j, group in enumerate(event_groups, 1):
                print(f"    {j}. {group['event_title']} ({group['news_count']} 則新聞)")
            
            # 計算剩餘新聞
            all_indices = set(range(1, len(news_items) + 1))
            used_indices = set()
            for group in event_groups:
                used_indices.update(group['news_indices'])
            remaining_count = len(all_indices - used_indices)
            print(f"  保留在「其他新聞」: {remaining_count} 則")
            
            # 詢問是否處理（如果不是自動確認模式）
            if not test_mode and not auto_confirm:
                user_input = input(f"\n  是否處理主題 {topic_id}？(y/n/q=quit): ").strip().lower()
                if user_input == 'q':
                    print("\n⏹️ 使用者中斷處理")
                    break
                elif user_input != 'y':
                    print("  ✓ 已跳過")
                    continue
            
            # 創建新分支並移動新聞
            result = self.create_new_branches_and_move_news(
                topic_id, 
                other_branch_id, 
                event_groups, 
                test_mode
            )
            
            if result:
                results.append({
                    'topic_id': topic_id,
                    'original_news_count': len(news_items),
                    'created_branches': result['created_branches'],
                    'moved_news': result['moved_news'],
                    'remaining_news': remaining_count
                })
                print(f"  ✓ 完成: 創建 {result['created_branches']} 個分支，移動 {result['moved_news']} 則新聞")
        
        # 3. 輸出總結
        print("\n" + "=" * 60)
        print("處理完成 - 總結")
        print("=" * 60)
        print(f"處理主題數: {len(results)}")
        if results:
            total_branches = sum(r['created_branches'] for r in results)
            total_moved = sum(r['moved_news'] for r in results)
            print(f"總共創建: {total_branches} 個新分支")
            print(f"總共移動: {total_moved} 則新聞")
            
            print("\n詳細結果:")
            for r in results:
                print(f"\n主題 {r['topic_id']}:")
                print(f"  原始新聞數: {r['original_news_count']}")
                print(f"  創建分支: {r['created_branches']}")
                print(f"  移動新聞: {r['moved_news']}")
                print(f"  保留新聞: {r['remaining_news']}")
        
        return results


def main():
    """主程式入口"""
    print("🚀 「其他新聞」分支重新分群工具")
    print("📋 功能: 遍歷所有「其他新聞」分支，使用 AI 進行智能分群")
    print("=" * 60)
    
    # 檢查命令列參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test' or command == '--test' or command == '-t':
            # 測試模式
            try:
                regrouper = OtherNewsRegrouper()
                
                if len(sys.argv) > 2:
                    # 測試單一主題
                    topic_id = sys.argv[2]
                    regrouper.process_single_topic(topic_id, test_mode=True)
                else:
                    # 測試所有主題
                    regrouper.process_all_topics(test_mode=True)
            except Exception as e:
                print(f"❌ 測試失敗: {e}")
            return
        
        elif command == 'process' or command == '--process' or command == '-p':
            # 處理模式
            try:
                regrouper = OtherNewsRegrouper()
                
                if len(sys.argv) > 2:
                    # 處理單一主題
                    topic_id = sys.argv[2]
                    regrouper.process_single_topic(topic_id, test_mode=False)
                else:
                    # 處理所有主題
                    auto_confirm = '--auto' in sys.argv or '-a' in sys.argv
                    regrouper.process_all_topics(test_mode=False, auto_confirm=auto_confirm)
            except Exception as e:
                print(f"❌ 處理失敗: {e}")
            return
        
        elif command == 'help' or command == '--help' or command == '-h':
            # 顯示幫助
            print("\n使用方式:")
            print("  python other_news_regrouper.py                           # 互動模式")
            print("  python other_news_regrouper.py test                      # 測試所有主題（不寫入）")
            print("  python other_news_regrouper.py test <topic_id>           # 測試單一主題（不寫入）")
            print("  python other_news_regrouper.py process                   # 處理所有主題（會詢問確認）")
            print("  python other_news_regrouper.py process --auto            # 處理所有主題（自動確認）")
            print("  python other_news_regrouper.py process <topic_id>        # 處理單一主題")
            print("  python other_news_regrouper.py --help                    # 顯示此幫助")
            print("\n範例:")
            print("  python other_news_regrouper.py test                      # 測試所有主題")
            print("  python other_news_regrouper.py test 12345                # 測試主題 12345")
            print("  python other_news_regrouper.py process                   # 處理所有主題")
            print("  python other_news_regrouper.py process 12345             # 處理主題 12345")
            print("  python other_news_regrouper.py process --auto            # 自動處理所有主題")
            return
    
    # 互動模式
    try:
        regrouper = OtherNewsRegrouper()
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return
    
    print("\n請選擇處理模式:")
    print("1. 處理單一主題")
    print("2. 處理所有主題")
    print("3. 測試模式（查看分群結果，不寫入資料庫）")
    
    try:
        choice = input("\n請輸入選項 (1/2/3): ").strip()
        
        if choice == '1':
            topic_id = input("請輸入主題 ID: ").strip()
            if topic_id:
                regrouper.process_single_topic(topic_id)
            else:
                print("❌ 無效的主題 ID")
        
        elif choice == '2':
            print("\n處理所有主題模式")
            auto_confirm = input("是否自動確認所有操作？(y/n): ").strip().lower() == 'y'
            regrouper.process_all_topics(auto_confirm=auto_confirm)
        
        elif choice == '3':
            print("\n測試模式")
            test_choice = input("測試所有主題還是單一主題？(all/single): ").strip().lower()
            if test_choice == 'single':
                topic_id = input("請輸入主題 ID: ").strip()
                if topic_id:
                    regrouper.process_single_topic(topic_id, test_mode=True)
                else:
                    print("❌ 無效的主題 ID")
            else:
                regrouper.process_all_topics(test_mode=True)
        
        else:
            print("❌ 無效的選項")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷程式執行")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
    
    print("\n程式結束")


if __name__ == "__main__":
    main()
