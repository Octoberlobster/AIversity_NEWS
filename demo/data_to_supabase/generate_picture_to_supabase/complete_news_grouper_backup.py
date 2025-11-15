"""新聞事件分組器 - 完整版
使用 google.genai 進行智能分組
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請在 Picture_generate_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("請在 Picture_generate_system/.env 設定 GEMINI_API_KEY")
    sys.exit(1)

try:
    from supabase import create_client
    print("✓ Supabase 套件已載入")
except ImportError:
    print("請先安裝 supabase-py：pip install supabase-py postgrest-py")
    sys.exit(1)

try:
    import google.genai as genai
    print("✓ Google Genai 套件已載入")
except ImportError:
    print("請先安裝 google genai SDK：pip install google-genai")
    sys.exit(1)

class NewsEventGrouper:
    """新聞事件分組器"""
    
    # 常數設定
    MIN_BRANCH_SIZE = 5  # 每個分支最少需要的新聞數量
    OTHER_BRANCH_TITLE = "其他待分類新聞"  # 暫存區分支名稱
    
    def __init__(self):
        """初始化客戶端"""
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            print("✓ Gemini Client 初始化成功")
        except Exception as e:
            print(f"✗ Gemini Client 初始化失敗: {e}")
            # 使用 fallback 方法
            print("切換到 fallback 模式...")
            self.genai_client = None
        
    def fetch_existing_branches_for_topic(self, topic_id):
        """獲取某主題現有的所有分支資料"""
        try:
            print(f"  檢查主題 {topic_id} 的現有分支...")
            
            # 獲取該主題的所有分支
            branch_response = self.supabase.table('topic_branch').select(
                'topic_branch_id, topic_branch_title, topic_branch_content'
            ).eq('topic_id', topic_id).execute()
            
            if not branch_response.data:
                print(f"  → 該主題尚無分支")
                return []
            
            branches = []
            for branch in branch_response.data:
                branch_id = branch.get('topic_branch_id')
                
                # 獲取該分支包含的新聞
                news_map_response = self.supabase.table('topic_branch_news_map').select(
                    'story_id'
                ).eq('topic_branch_id', branch_id).execute()
                
                story_ids = [item['story_id'] for item in news_map_response.data] if news_map_response.data else []
                
                branches.append({
                    'branch_id': branch_id,
                    'title': branch.get('topic_branch_title'),
                    'content': branch.get('topic_branch_content'),
                    'story_ids': story_ids,
                    'news_count': len(story_ids)
                })
            
            print(f"  → 找到 {len(branches)} 個現有分支")
            for i, branch in enumerate(branches, 1):
                print(f"    分支 {i}: {branch['title']} ({branch['news_count']} 則新聞)")
            
            return branches
            
        except Exception as e:
            print(f"  ✗ 獲取現有分支時發生錯誤: {e}")
            return []
    
    def fetch_topic_news_map_from_supabase(self):
        """從 Supabase 的 topic_news_map 表獲取主題新聞映射"""
        try:
            print("開始從 topic_news_map 表獲取資料...")
            response = self.supabase.table('topic_news_map').select(
                'topic_id, story_id'
            ).execute()
            
            if response.data:
                print(f"✓ 成功獲取 {len(response.data)} 筆主題新聞映射資料")
                return response.data
            else:
                print("✗ topic_news_map 表無資料")
                return []
                
        except Exception as e:
            print(f"✗ 獲取 topic_news_map 資料時發生錯誤: {e}")
            return []
    
    def group_by_topic_id(self, topic_news_map):
        """根據 topic_id 將新聞分組"""
        topic_groups = {}
        
        for item in topic_news_map:
            topic_id = item.get('topic_id')
            story_id = item.get('story_id')
            
            if topic_id and story_id:
                if topic_id not in topic_groups:
                    topic_groups[topic_id] = []
                topic_groups[topic_id].append(story_id)
        
        print(f"✓ 根據 topic_id 分成 {len(topic_groups)} 個主題組")
        for topic_id, story_ids in topic_groups.items():
            print(f"  主題 {topic_id}: {len(story_ids)} 則新聞")
        
        return topic_groups
    
    def read_story_ids_from_json(self, json_file_path):
        """從 JSON 檔案讀取 story_id 列表"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            story_ids = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        story_id = (item.get('story_id') or 
                                  item.get('id') or 
                                  item.get('storyId'))
                        if story_id:
                            story_ids.append(str(story_id))
            
            print(f"從 {json_file_path} 讀取到 {len(story_ids)} 個 story_id")
            return list(set(story_ids))  # 去重
            
        except Exception as e:
            print(f"讀取 JSON 檔案時發生錯誤: {e}")
            return []
    
    def fetch_news_from_supabase(self, story_ids):
        """從 Supabase 獲取新聞內容"""
        news_items = []
        
        print(f"開始從 Supabase 獲取 {len(story_ids)} 則新聞...")
        
        for i, story_id in enumerate(story_ids, 1):
            try:
                response = self.supabase.table('single_news').select(
                    'story_id, news_title, long'
                ).eq('story_id', story_id).execute()
                
                if response.data and len(response.data) > 0:
                    news_data = response.data[0]
                    news_items.append({
                        'story_id': news_data.get('story_id'),
                        'news_title': news_data.get('news_title', ''),
                        'content': news_data.get('long', '')
                    })
                    print(f"✓ {i}/{len(story_ids)}: 成功獲取 story_id {story_id}")
                else:
                    print(f"✗ {i}/{len(story_ids)}: story_id {story_id} 未找到對應新聞")
                    
            except Exception as e:
                print(f"✗ {i}/{len(story_ids)}: 獲取 story_id {story_id} 時發生錯誤: {e}")
                
            # 避免請求過於頻繁
            time.sleep(0.1)
        
        print(f"成功獲取 {len(news_items)} 則新聞內容")
        return news_items
    
    def check_if_news_fits_branch(self, news_item, branch_news_items):
        """使用 AI 檢查新新聞是否適合加入現有分支"""
        if not self.genai_client:
            return False
        
        # 準備現有分支的新聞摘要
        branch_summaries = []
        for i, news in enumerate(branch_news_items[:3], 1):
            title = news['news_title'][:50]
            content = news['content'][:100]
            branch_summaries.append(f"新聞{i}: {title} - {content}...")
        
        # 新新聞摘要
        new_title = news_item['news_title'][:50]
        new_content = news_item['content'][:100]
        
        prompt = f"""
判斷以下「新新聞」是否與「現有分支新聞」屬於同一事件或高度相關。

【現有分支新聞】
{chr(10).join(branch_summaries)}

【新新聞】
標題: {new_title}
內容: {new_content}...

請回答 YES 或 NO：
- YES: 新新聞與現有分支高度相關，可以加入
- NO: 新新聞與現有分支不相關，不應加入

只回傳 YES 或 NO，不要其他文字。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            answer = response.text.strip().upper()
            return 'YES' in answer
        except Exception as e:
            print(f"    ✗ AI 判斷時發生錯誤: {e}")
            return False
    
    def group_news_by_events_ai_with_min_size(self, news_items, min_size=5):
        """使用 Gemini AI 將新聞分組，確保每組至少有 min_size 則新聞
        
        Args:
            news_items: 新聞列表
            min_size: 每組最少新聞數量（預設5則）
        
        Returns:
            符合最小規模的分組 + "其他"暫存分組
        """
        if not self.genai_client or not news_items:
            return self.simple_group_news(news_items)
        
        print(f"  使用 AI 分組（最小規模: {min_size} 則新聞）...")
        
        # 先用原有邏輯分組
        raw_groups = self.group_news_by_events_ai(news_items)
        
        # 篩選出符合最小規模的分組
        valid_groups = []
        small_groups_news = []  # 收集不足最小規模的新聞
        
        for group in raw_groups:
            if group['news_count'] >= min_size:
                valid_groups.append(group)
                print(f"    ✓ 分支「{group['event_title']}」符合規模 ({group['news_count']} 則)")
            else:
                print(f"    ✗ 分支「{group['event_title']}」不足規模 ({group['news_count']} 則)，新聞將放入暫存區")
                small_groups_news.extend(group['news_items'])
        
        # 將不足規模的新聞放入"其他"暫存區
        if small_groups_news:
            other_branch = {
                'event_id': str(uuid.uuid4()),
                'event_title': self.OTHER_BRANCH_TITLE,
                'event_summary': f'包含 {len(small_groups_news)} 則待重新分類的新聞（不足 {min_size} 則無法成為獨立分支）',
                'news_count': len(small_groups_news),
                'news_items': small_groups_news,
                'is_other': True  # 標記為暫存區
            }
            valid_groups.append(other_branch)
            print(f"    → 創建暫存區「{self.OTHER_BRANCH_TITLE}」({len(small_groups_news)} 則新聞)")
        
        return valid_groups
    
    def group_news_by_events_ai(self, news_items):
        """使用 Gemini AI 將新聞分組為事件分支（原始方法，不考慮最小規模）"""
        if not self.genai_client or not news_items:
            return self.simple_group_news(news_items)
        
        print("開始使用 Gemini AI 分析新聞事件...")
        
        # 準備新聞摘要資料供模型分析
        news_summaries = []
        for i, news in enumerate(news_items):
            title = news['news_title'][:100]  # 增加標題長度
            content = news['content'][:300]   # 增加內容長度以提供更多細節
            summary = f"新聞{i+1}：標題：{title}；內容：{content}..."
            news_summaries.append(summary)
        
        # 構建提示語
        prompt = f"""
# 角色
你是一位頂尖的新聞分析專家，擁有超過20年的產業經驗。你的核心能力是快速洞察大量快訊背後的核心事件脈絡，將看似獨立的報導整合成清晰、有邏輯的事件群組，並為其命名精準的標題。

# 核心任務
分析下方提供的 {len(news_items)} 則新聞，將它們依據「核心事件」進行合併分組。

# 兩大絕對原則 (必須嚴格遵守)
1.  **禁止任何形式的「其他」或「未分類」分組**：所有新聞都必須被歸入一個有具體事件意義的分組。這條原則沒有例外。
2.  **杜絕單一新聞分組**：每個分組必須包含至少 2 則新聞。如果某則新聞看似獨立，你必須重新審視所有新聞，找出與它最相關的事件並將其併入。你的職責是找出關聯，而非製造孤島。

# 新聞資料
{chr(1000).join(news_summaries)}

# 執行步驟 (請在內部依序思考，僅最終輸出 JSON)

### 步驟一：初步掃描與主題識別
快速閱讀全部 {len(news_items)} 則新聞，為每一則新聞標記出 2-3 個核心關鍵詞（例如：人物、地點、事件類型）。

### 步驟二：強制關聯與合併
這是最重要的步驟。檢視所有新聞的關鍵詞，開始強制尋找關聯性並進行合併：
- **因果關聯**：事件A是否導致了事件B？它們應屬同一組。
- **人物/地點關聯**：不同新聞是否涉及相同的關鍵人物、公司或地點？它們應屬同一組。
- **主題延伸**：報導A是否是事件B的後續發展或不同面向的探討？它們應屬同一組。
- **建立草稿分組**：基於以上關聯，建立 3-5 個草稿分組。**你的預設行為應該是合併，而不是拆分**。

### 步驟三：審核與調整
檢查你的草稿分組是否違反了「兩大絕對原則」：
- 是否存在只有一則新聞的分組？若有，立刻將該新聞併入最相關的現有分組中，並調整該組的標題與摘要以涵蓋新內容。
- 是否所有新聞都已分配完畢？確保編號 1 到 {len(news_items)} 都被分配。
- 分組數量是否在 3-5 個之間？這是最佳實踐，除非新聞內容極度單一或分散。

### 步驟四：生成最終輸出
在你確認所有原則都已滿足後，才將最終結果格式化為 JSON。

# 最終輸出要求
**僅回傳標準的 JSON 格式**，不要包含任何説明、註解或 ```json ... ``` 標記。

{{
  "groups": [
    {{
      "event_title": "精煉的核心事件標題 (10字內)",
      "event_summary": "全面且客觀地總結該事件的核心內容 (80字內)",
      "news_indices": [/* 新聞編號陣列，從 1 開始，例如 [1, 5, 8] */]
    }},
    {{
      "event_title": "另一個事件的精煉標題 (10字內)",
      "event_summary": "另一個事件的核心內容總結",
      "news_indices": [/* ... */]
    }}
  ]
}}

分組原則：
1. 以主要事件或政策為核心分組
2. 同一事件的不同發展階段可以放在同一組

4. 事件標題要能涵蓋組內所有新聞的共同主題
5. news_indices 對應新聞的編號（從1開始）
6. 確保所有新聞都被分配到某個分組
7. 只回傳 JSON，不要其他說明文字

"""

        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            result_text = response.text.strip()
            
            # 解析 JSON 結果
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            groups = result.get('groups', [])
            
            print(f"AI 分析完成，共分為 {len(groups)} 個事件分支")
            
            # 轉換為最終格式，並確保每則新聞只出現在一個分支
            event_groups = []
            used_news_indices = set()  # 追蹤已使用的新聞索引
            
            for group in groups:
                event_title = group.get('event_title', '未命名事件')
                event_summary = group.get('event_summary', '')
                news_indices = group.get('news_indices', [])
                
                # 獲取對應的新聞項目，排除已使用的新聞
                group_news = []
                for idx in news_indices:
                    if 1 <= idx <= len(news_items) and idx not in used_news_indices:
                        group_news.append(news_items[idx - 1])  # 轉換為0-based索引
                        used_news_indices.add(idx)  # 標記為已使用
                
                if group_news:  # 只添加有新聞的分組
                    event_groups.append({
                        'event_id': str(uuid.uuid4()),
                        'event_title': event_title,
                        'event_summary': event_summary,
                        'news_count': len(group_news),
                        'news_items': group_news
                    })
            
            # 檢查是否有未分配的新聞
            all_indices = set(range(1, len(news_items) + 1))
            unused_indices = all_indices - used_news_indices
            
            if unused_indices:
                # 將未分配的新聞創建為一個額外的分組
                unused_news = [news_items[idx - 1] for idx in unused_indices]
                event_groups.append({
                    'event_id': str(uuid.uuid4()),
                    'event_title': '其他相關新聞',
                    'event_summary': f'包含 {len(unused_news)} 則未被其他分支包含的相關新聞',
                    'news_count': len(unused_news),
                    'news_items': unused_news
                })
                print(f"注意：有 {len(unused_indices)} 則新聞未被 AI 分組，已自動創建「其他相關新聞」分支")
            
            return event_groups
            
        except Exception as e:
            print(f"AI 分析時發生錯誤: {e}")
            print("切換到簡單分組模式...")
            return self.simple_group_news(news_items)
    
    def simple_group_news(self, news_items):
        """簡單的新聞分組（不使用 AI）"""
        return [{
            'event_id': str(uuid.uuid4()),
            'event_title': '綜合新聞事件',
            'event_summary': f'包含 {len(news_items)} 則相關新聞的綜合事件',
            'news_count': len(news_items),
            'news_items': news_items
        }]
    
    def save_to_database(self, event_groups, save_mode="both"):
        """將事件分支和新聞映射存入資料庫
        
        Args:
            event_groups: 處理好的事件分組資料
            save_mode: 儲存模式 - "preview"(僅預覽), "database"(僅資料庫), "both"(預覽+資料庫)
        """
        try:
            print(f"\n開始資料庫儲存流程 (模式: {save_mode})...")
            
            # 準備兩個資料表的資料
            topic_branch_news_map_data = []
            topic_branch_data = []
            
            for topic_group in event_groups:
                topic_id = topic_group.get('topic_id')
                sub_events = topic_group.get('sub_events', [])
                
                for sub_event in sub_events:
                    topic_branch_id = sub_event.get('event_id')
                    topic_branch_title = sub_event.get('event_title')
                    topic_branch_content = sub_event.get('event_summary')
                    news_items = sub_event.get('news_items', [])
                    
                    # 1. 準備 topic_branch 資料
                    if topic_id and topic_branch_id and topic_branch_title:
                        topic_branch_data.append({
                            'topic_id': topic_id,
                            'topic_branch_id': topic_branch_id,
                            'topic_branch_title': topic_branch_title,
                            'topic_branch_content': topic_branch_content or ''
                        })
                    
                    # 2. 準備 topic_branch_news_map 資料
                    for news_item in news_items:
                        story_id = news_item.get('story_id')
                        if topic_branch_id and story_id:
                            topic_branch_news_map_data.append({
                                'topic_branch_id': topic_branch_id,
                                'story_id': story_id
                            })
            
            print(f"準備資料: {len(topic_branch_data)} 個分支, {len(topic_branch_news_map_data)} 筆新聞對應")
            
            # 根據模式執行相應操作
            if save_mode in ["preview", "both"]:
                self._save_database_preview(topic_branch_data, topic_branch_news_map_data)
            
            if save_mode in ["database", "both"]:
                self._save_to_actual_database(topic_branch_data, topic_branch_news_map_data)
                
        except Exception as e:
            print(f"✗ 資料庫儲存流程發生錯誤: {e}")
    
    def _save_database_preview(self, topic_branch_data, topic_branch_news_map_data):
        """儲存資料庫預覽檔案"""
        try:
            print("\n--- 生成資料庫預覽檔案 ---")
            
            # 儲存 topic_branch 預覽
            topic_branch_file = "database_preview_topic_branch.json"
            with open(topic_branch_file, 'w', encoding='utf-8') as f:
                json.dump(topic_branch_data, f, ensure_ascii=False, indent=2)
            print(f"✓ topic_branch 預覽已儲存: {topic_branch_file}")
            print(f"  共 {len(topic_branch_data)} 個主題分支")
            
            # 儲存 topic_branch_news_map 預覽
            topic_branch_news_map_file = "database_preview_topic_branch_news_map.json"
            with open(topic_branch_news_map_file, 'w', encoding='utf-8') as f:
                json.dump(topic_branch_news_map_data, f, ensure_ascii=False, indent=2)
            print(f"✓ topic_branch_news_map 預覽已儲存: {topic_branch_news_map_file}")
            print(f"  共 {len(topic_branch_news_map_data)} 筆對應關係")
            
            # 顯示範例
            print("\n【topic_branch 範例】")
            for i, item in enumerate(topic_branch_data[:3], 1):
                print(f"{i}. topic_id: {item['topic_id']}")
                print(f"   topic_branch_id: {item['topic_branch_id']}")
                print(f"   topic_branch_title: {item['topic_branch_title']}")
                print(f"   topic_branch_content: {item['topic_branch_content'][:50]}...")
                print()
            
            print("【topic_branch_news_map 範例】")
            for i, item in enumerate(topic_branch_news_map_data[:5], 1):
                print(f"{i}. {item['topic_branch_id']} <-> {item['story_id']}")
            
            if len(topic_branch_news_map_data) > 5:
                print(f"... 還有 {len(topic_branch_news_map_data) - 5} 筆資料")
            
        except Exception as e:
            print(f"✗ 生成預覽檔案時發生錯誤: {e}")
    
    def _save_to_actual_database(self, topic_branch_data, topic_branch_news_map_data):
        """儲存到實際資料庫"""
        try:
            print("\n--- 開始儲存到實際資料庫 ---")
            
            # 儲存 topic_branch 資料
            print("1. 儲存 topic_branch 資料...")
            if topic_branch_data:
                # 清除現有資料（可選 - 根據需求決定）
                # self.supabase.table('topic_branch').delete().neq('topic_id', '').execute()
                
                batch_size = 50
                success_count = 0
                
                for i in range(0, len(topic_branch_data), batch_size):
                    batch = topic_branch_data[i:i + batch_size]
                    try:
                        response = self.supabase.table('topic_branch').upsert(batch).execute()
                        if response.data:
                            success_count += len(batch)
                            print(f"   ✓ topic_branch 第 {i//batch_size + 1} 批 ({len(batch)} 筆)")
                        else:
                            print(f"   ✗ topic_branch 第 {i//batch_size + 1} 批插入失敗")
                    except Exception as e:
                        print(f"   ✗ topic_branch 第 {i//batch_size + 1} 批發生錯誤: {e}")
                
                print(f"   → topic_branch 成功儲存: {success_count}/{len(topic_branch_data)} 筆")
            
            # 儲存 topic_branch_news_map 資料
            print("2. 儲存 topic_branch_news_map 資料...")
            if topic_branch_news_map_data:
                # 清除現有資料（可選）
                # self.supabase.table('topic_branch_news_map').delete().neq('topic_branch_id', '').execute()
                
                batch_size = 100
                success_count = 0
                
                for i in range(0, len(topic_branch_news_map_data), batch_size):
                    batch = topic_branch_news_map_data[i:i + batch_size]
                    try:
                        response = self.supabase.table('topic_branch_news_map').upsert(batch).execute()
                        if response.data:
                            success_count += len(batch)
                            print(f"   ✓ topic_branch_news_map 第 {i//batch_size + 1} 批 ({len(batch)} 筆)")
                        else:
                            print(f"   ✗ topic_branch_news_map 第 {i//batch_size + 1} 批插入失敗")
                    except Exception as e:
                        print(f"   ✗ topic_branch_news_map 第 {i//batch_size + 1} 批發生錯誤: {e}")
                
                print(f"   → topic_branch_news_map 成功儲存: {success_count}/{len(topic_branch_news_map_data)} 筆")
            
            print("\n✅ 資料庫儲存完成！")
            
        except Exception as e:
            print(f"✗ 儲存到實際資料庫時發生錯誤: {e}")
    
    def save_to_json(self, event_groups, output_path):
        """儲存結果到 JSON 檔案"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(event_groups, f, ensure_ascii=False, indent=2)
            print(f"結果已儲存至: {output_path}")
        except Exception as e:
            print(f"儲存檔案時發生錯誤: {e}")
    
    def process_topic_with_incremental_update(self, topic_id, new_story_ids, existing_branches):
        """增量更新：處理新新聞與現有分支的整合
        
        Args:
            topic_id: 主題 ID
            new_story_ids: 新加入的 story_id 列表
            existing_branches: 現有的分支資料
        
        Returns:
            更新後的分支結構 + 需要刪除的舊分支 ID
        """
        print(f"\n  【增量更新模式】處理 {len(new_story_ids)} 則新新聞")
        
        # 1. 獲取新新聞內容
        new_news_items = self.fetch_news_from_supabase(new_story_ids)
        if not new_news_items:
            print("  ✗ 未獲取到新新聞內容")
            return None, []
        
        # 2. 提取"其他"暫存區（如果存在）
        other_branch = None
        normal_branches = []
        
        for branch in existing_branches:
            if self.OTHER_BRANCH_TITLE in branch['title']:
                other_branch = branch
                print(f"  → 找到暫存區分支: {branch['news_count']} 則新聞")
            else:
                normal_branches.append(branch)
        
        # 3. 嘗試將新新聞加入現有分支
        unmatched_new_news = []
        branch_additions = {}  # {branch_id: [news_items to add]}
        
        print(f"\n  檢查新新聞是否可加入現有 {len(normal_branches)} 個分支...")
        for new_news in new_news_items:
            matched = False
            
            for branch in normal_branches:
                # 獲取該分支的新聞內容用於判斷
                branch_news = self.fetch_news_from_supabase(branch['story_ids'][:5])  # 取前5則代表
                
                if self.check_if_news_fits_branch(new_news, branch_news):
                    print(f"    ✓ 新聞「{new_news['news_title'][:30]}」可加入分支「{branch['title']}」")
                    if branch['branch_id'] not in branch_additions:
                        branch_additions[branch['branch_id']] = []
                    branch_additions[branch['branch_id']].append(new_news)
                    matched = True
                    break
            
            if not matched:
                print(f"    ○ 新聞「{new_news['news_title'][:30]}」未匹配現有分支")
                unmatched_new_news.append(new_news)
        
        # 4. 合併暫存區新聞 + 未匹配的新新聞
        candidate_for_regroup = unmatched_new_news.copy()
        if other_branch:
            other_news = self.fetch_news_from_supabase(other_branch['story_ids'])
            candidate_for_regroup.extend(other_news)
            print(f"\n  合併暫存區 {len(other_news)} 則 + 新未匹配 {len(unmatched_new_news)} 則 = {len(candidate_for_regroup)} 則")
        
        # 5. 判斷是否需要重新分組
        need_regroup = False
        branches_to_delete = []
        new_branches = []
        
        if len(candidate_for_regroup) >= self.MIN_BRANCH_SIZE:
            print(f"\n  ★ 暫存區+新新聞共 {len(candidate_for_regroup)} 則，達到最小規模，嘗試重新分組...")
            need_regroup = True
            
            # 重新分組這些新聞
            regrouped = self.group_news_by_events_ai_with_min_size(
                candidate_for_regroup, 
                min_size=self.MIN_BRANCH_SIZE
            )
            
            # 標記舊的"其他"分支需要刪除
            if other_branch:
                branches_to_delete.append(other_branch['branch_id'])
            
            new_branches = regrouped
        
        elif candidate_for_regroup:
            # 數量不足，放回暫存區
            print(f"\n  → 暫存區+新新聞共 {len(candidate_for_regroup)} 則，不足最小規模，繼續放入暫存區")
            other_branch_new = {
                'event_id': other_branch['branch_id'] if other_branch else str(uuid.uuid4()),
                'event_title': self.OTHER_BRANCH_TITLE,
                'event_summary': f'包含 {len(candidate_for_regroup)} 則待重新分類的新聞',
                'news_count': len(candidate_for_regroup),
                'news_items': candidate_for_regroup,
                'is_other': True
            }
            new_branches = [other_branch_new]
        
        # 6. 組合最終結果
        result_branches = []
        
        # 加入更新後的現有分支
        for branch in normal_branches:
            branch_dict = {
                'event_id': branch['branch_id'],
                'event_title': branch['title'],
                'event_summary': branch['content'],
                'news_count': branch['news_count'],
                'news_items': []  # 實際寫入時會補齊
            }
            
            # 如果該分支有新增新聞
            if branch['branch_id'] in branch_additions:
                added_count = len(branch_additions[branch['branch_id']])
                branch_dict['news_count'] += added_count
                branch_dict['news_items'] = branch_additions[branch['branch_id']]
                print(f"    → 分支「{branch['title']}」將新增 {added_count} 則新聞")
            
            result_branches.append(branch_dict)
        
        # 加入新分組的分支
        result_branches.extend(new_branches)
        
        return result_branches, branches_to_delete
    
    def process_from_topic_map(self, output_path, save_to_db=True, incremental_mode=False):
        """使用 topic_news_map 的處理流程
        
        Args:
            output_path: JSON 輸出檔案路徑
            save_to_db: 是否儲存到資料庫 (True=儲存, False=僅預覽)
            incremental_mode: 是否使用增量更新模式（檢查現有分支並智能整合新新聞）
        """
        print("=" * 60)
        if incremental_mode:
            print("新聞事件分組器 - 增量更新模式（最小分支規模: 5 則）")
        else:
            print("新聞事件分組器 - 從 topic_news_map 開始處理")
        print("=" * 60)
        
        # 1. 從 topic_news_map 獲取資料
        topic_news_map = self.fetch_topic_news_map_from_supabase()
        if not topic_news_map:
            print("未獲取到 topic_news_map 資料，程式結束")
            return
        
        # 2. 根據 topic_id 分組
        topic_groups = self.group_by_topic_id(topic_news_map)
        if not topic_groups:
            print("未找到有效的主題分組，程式結束")
            return
        
        # 3. 為每個主題組獲取新聞內容，然後再用 AI 做細分
        all_topic_events = []
        all_branches_to_delete = []  # 收集需要刪除的舊分支 ID
        
        for topic_id, story_ids in topic_groups.items():
            print(f"\n{'='*60}")
            print(f"處理主題 {topic_id} ({len(story_ids)} 則新聞)")
            print(f"{'='*60}")
            
            # 【增量模式】檢查現有分支
            if incremental_mode:
                existing_branches = self.fetch_existing_branches_for_topic(topic_id)
                
                if existing_branches:
                    # 找出新增的新聞（不在現有分支中的）
                    existing_story_ids = set()
                    for branch in existing_branches:
                        existing_story_ids.update(branch['story_ids'])
                    
                    new_story_ids = [sid for sid in story_ids if sid not in existing_story_ids]
                    
                    if new_story_ids:
                        print(f"  發現 {len(new_story_ids)} 則新新聞（現有 {len(existing_story_ids)} 則）")
                        
                        # 使用增量更新邏輯
                        updated_branches, branches_to_delete = self.process_topic_with_incremental_update(
                            topic_id, new_story_ids, existing_branches
                        )
                        
                        if branches_to_delete:
                            all_branches_to_delete.extend(branches_to_delete)
                            print(f"\n  ⚠️ 需要刪除 {len(branches_to_delete)} 個舊分支（將重新分組）")
                        
                        if updated_branches:
                            # 生成主題標題
                            all_news_items = self.fetch_news_from_supabase(story_ids)
                            topic_title = self.generate_topic_title(all_news_items)
                            
                            topic_event = {
                                'topic_id': topic_id,
                                'topic_title': topic_title,
                                'sub_events': updated_branches
                            }
                            all_topic_events.append(topic_event)
                            continue
                    else:
                        print("  → 無新新聞，保持現有分支結構")
                        
                        # 保留現有分支結構到結果中
                        all_news_items = self.fetch_news_from_supabase(story_ids)
                        topic_title = self.generate_topic_title(all_news_items)
                        
                        # 將現有分支轉換為標準格式
                        sub_events = []
                        for branch in existing_branches:
                            branch_news = self.fetch_news_from_supabase(branch['story_ids'])
                            sub_events.append({
                                'event_id': branch['branch_id'],
                                'event_title': branch['title'],
                                'event_summary': branch['content'],
                                'news_count': len(branch_news),
                                'news_items': branch_news,
                                'is_other': self.OTHER_BRANCH_TITLE in branch['title']
                            })
                        
                        topic_event = {
                            'topic_id': topic_id,
                            'topic_title': topic_title,
                            'sub_events': sub_events,
                            'status': 'unchanged'  # 標記為未變更
                        }
                        all_topic_events.append(topic_event)
                        continue
            
            # 【標準模式或首次處理】
            # 獲取該主題的新聞內容
            news_items = self.fetch_news_from_supabase(story_ids)
            
            if not news_items:
                print(f"✗ 主題 {topic_id}: 未獲取到有效新聞內容")
                continue
            
            # 為該主題生成總體標題
            topic_title = self.generate_topic_title(news_items)
            print(f"✓ 主題標題: {topic_title}")
            
            # 根據新聞數量決定處理方式
            if len(news_items) < self.MIN_BRANCH_SIZE:
                # 數量不足最小規模，直接放入暫存區
                print(f"  → 新聞數量 {len(news_items)} 不足最小規模 {self.MIN_BRANCH_SIZE}，放入暫存區")
                topic_summary = self.generate_topic_summary(news_items)
                topic_event = {
                    'topic_id': topic_id,
                    'topic_title': topic_title,
                    'sub_events': [
                        {
                            'event_id': str(uuid.uuid4()),
                            'event_title': self.OTHER_BRANCH_TITLE,
                            'event_summary': f'包含 {len(news_items)} 則待重新分類的新聞',
                            'news_count': len(news_items),
                            'news_items': news_items,
                            'is_other': True
                        }
                    ]
                }
                all_topic_events.append(topic_event)
            
            else:
                # 新聞數量足夠，使用 AI 進行細分（考慮最小規模）
                print(f"  正在對 {len(news_items)} 則新聞進行 AI 細分（最小規模: {self.MIN_BRANCH_SIZE}）...")
                sub_events = self.group_news_by_events_ai_with_min_size(
                    news_items, 
                    min_size=self.MIN_BRANCH_SIZE
                )
                
                # 為每個子事件添加 topic 相關資訊
                for sub_event in sub_events:
                    sub_event['topic_id'] = topic_id
                
                topic_event = {
                    'topic_id': topic_id,
                    'topic_title': topic_title,
                    'sub_events': sub_events
                }
                all_topic_events.append(topic_event)
                
                print(f"\n  ✓ 細分結果:")
                for i, sub_event in enumerate(sub_events, 1):
                    is_other = sub_event.get('is_other', False)
                    marker = "📦" if is_other else "📌"
                    print(f"    {marker} 分支 {i}: {sub_event['event_title']} ({sub_event['news_count']} 則新聞)")
        
        # 4. 儲存結果到 JSON
        self.save_to_json(all_topic_events, output_path)
        
        # 5. 輸出詳細預覽到終端
        print("\n" + "=" * 80)
        print("📊 分組結果預覽（輸出到終端）")
        print("=" * 80)
        
        for i, topic in enumerate(all_topic_events, 1):
            print(f"\n【主題 {i}】{topic['topic_title']}")
            print(f"  主題 ID: {topic['topic_id']}")
            print(f"  分支數量: {len(topic['sub_events'])}")
            
            for j, sub_event in enumerate(topic['sub_events'], 1):
                is_other = sub_event.get('is_other', False)
                marker = "📦 [暫存區]" if is_other else "📌"
                
                print(f"\n  {marker} 分支 {j}: {sub_event['event_title']}")
                print(f"     分支 ID: {sub_event['event_id']}")
                print(f"     新聞數量: {sub_event['news_count']} 則")
                print(f"     摘要: {sub_event['event_summary'][:80]}...")
                
                # 列出前3則新聞標題
                news_items = sub_event.get('news_items', [])
                if news_items:
                    print(f"     包含新聞:")
                    for k, news in enumerate(news_items[:3], 1):
                        title = news.get('news_title', '')[:50]
                        print(f"       {k}. {title}{'...' if len(news.get('news_title', '')) > 50 else ''}")
                    if len(news_items) > 3:
                        print(f"       ... 還有 {len(news_items) - 3} 則新聞")
        
        # 6. 顯示需要刪除的舊分支（如果有）
        if all_branches_to_delete:
            print("\n" + "=" * 80)
            print("⚠️  需要刪除的舊分支 ID（將在寫入資料庫時執行）")
            print("=" * 80)
            for branch_id in all_branches_to_delete:
                print(f"  - {branch_id}")
        
        # 7. 儲存到資料庫或僅生成預覽
        print("\n" + "=" * 80)
        if save_to_db:
            print("⚠️  資料庫寫入已停用（根據需求先預覽到終端）")
            print("=" * 80)
            print("如需寫入資料庫，請修改 main() 中的 save_to_db 參數為 True")
        else:
            print("📋 僅預覽模式（不會寫入資料庫）")
            print("=" * 80)
        
        # 8. 檢查並重新處理不足規模的分支
        print("\n" + "=" * 80)
        print("🔍 檢查不足規模的分支（非暫存區）")
        print("=" * 80)
        
        undersized_branches = []
        for topic in all_topic_events:
            topic_id = topic['topic_id']
            for sub_event in topic['sub_events']:
                # 只檢查非暫存區的分支
                if not sub_event.get('is_other', False):
                    if sub_event['news_count'] < self.MIN_BRANCH_SIZE:
                        undersized_branches.append({
                            'topic_id': topic_id,
                            'topic_title': topic['topic_title'],
                            'branch': sub_event
                        })
                        print(f"⚠️  主題「{topic['topic_title']}」的分支「{sub_event['event_title']}」")
                        print(f"    只有 {sub_event['news_count']} 則新聞（不足 {self.MIN_BRANCH_SIZE} 則）")
        
        if undersized_branches:
            print(f"\n發現 {len(undersized_branches)} 個不足規模的分支，將重新分組...")
            print("=" * 80)
            
            # 按主題分組不足規模的分支
            undersized_by_topic = {}
            for item in undersized_branches:
                topic_id = item['topic_id']
                if topic_id not in undersized_by_topic:
                    undersized_by_topic[topic_id] = []
                undersized_by_topic[topic_id].append(item['branch'])
            
            # 對每個主題的不足規模分支進行處理
            for topic_id, branches in undersized_by_topic.items():
                print(f"\n處理主題 {topic_id} 的不足規模分支...")
                
                # 收集這些分支的所有新聞
                all_undersized_news = []
                branches_to_remove = []
                
                for branch in branches:
                    all_undersized_news.extend(branch['news_items'])
                    branches_to_remove.append(branch['event_id'])
                    print(f"  - 拆解分支「{branch['event_title']}」({branch['news_count']} 則)")
                
                print(f"\n  共收集 {len(all_undersized_news)} 則新聞，嘗試重新分組...")
                
                # 找到對應的主題並更新
                for topic in all_topic_events:
                    if topic['topic_id'] == topic_id:
                        # 移除不足規模的分支
                        topic['sub_events'] = [
                            sub for sub in topic['sub_events'] 
                            if sub['event_id'] not in branches_to_remove
                        ]
                        
                        # 尋找該主題的暫存區分支
                        other_branch = None
                        for sub in topic['sub_events']:
                            if sub.get('is_other', False):
                                other_branch = sub
                                break
                        
                        # 合併到暫存區
                        if other_branch:
                            print(f"  → 將 {len(all_undersized_news)} 則新聞併入現有暫存區")
                            other_branch['news_items'].extend(all_undersized_news)
                            other_branch['news_count'] += len(all_undersized_news)
                            other_branch['event_summary'] = f'包含 {other_branch["news_count"]} 則待重新分類的新聞'
                            
                            # 檢查是否達到最小規模可以重新分組
                            if other_branch['news_count'] >= self.MIN_BRANCH_SIZE:
                                print(f"  ★ 暫存區已達 {other_branch['news_count']} 則，嘗試重新分組...")
                                
                                regrouped = self.group_news_by_events_ai_with_min_size(
                                    other_branch['news_items'],
                                    min_size=self.MIN_BRANCH_SIZE
                                )
                                
                                # 移除舊的暫存區
                                topic['sub_events'] = [
                                    sub for sub in topic['sub_events']
                                    if not sub.get('is_other', False)
                                ]
                                
                                # 加入重新分組的結果
                                for new_branch in regrouped:
                                    new_branch['topic_id'] = topic_id
                                topic['sub_events'].extend(regrouped)
                                
                                print(f"  ✓ 重新分組完成，產生 {len(regrouped)} 個新分支")
                                for i, branch in enumerate(regrouped, 1):
                                    is_other = branch.get('is_other', False)
                                    marker = "📦" if is_other else "📌"
                                    print(f"    {marker} {branch['event_title']} ({branch['news_count']} 則)")
                        else:
                            # 創建新的暫存區
                            print(f"  → 創建新暫存區容納 {len(all_undersized_news)} 則新聞")
                            new_other = {
                                'event_id': str(uuid.uuid4()),
                                'event_title': self.OTHER_BRANCH_TITLE,
                                'event_summary': f'包含 {len(all_undersized_news)} 則待重新分類的新聞',
                                'news_count': len(all_undersized_news),
                                'news_items': all_undersized_news,
                                'is_other': True,
                                'topic_id': topic_id
                            }
                            topic['sub_events'].append(new_other)
                        
                        # 記錄需要刪除的舊分支
                        all_branches_to_delete.extend(branches_to_remove)
                        break
            
            print("\n✅ 不足規模分支處理完成")
        else:
            print("✓ 所有正式分支都符合最小規模要求")
        
        # 9. 輸出統計資訊
        print("\n" + "=" * 80)
        print("📈 統計摘要")
        print("=" * 80)
        print(f"主題數量: {len(topic_groups)}")
        print(f"成功處理的主題: {len(all_topic_events)}")
        
        total_sub_events = sum(len(topic['sub_events']) for topic in all_topic_events)
        total_normal_branches = sum(
            1 for topic in all_topic_events 
            for sub in topic['sub_events'] 
            if not sub.get('is_other', False)
        )
        total_other_branches = total_sub_events - total_normal_branches
        total_news = sum(
            sum(sub_event['news_count'] for sub_event in topic['sub_events'])
            for topic in all_topic_events
        )
        
        print(f"總分支數量: {total_sub_events}")
        print(f"  - 正式分支: {total_normal_branches}")
        print(f"  - 暫存區分支: {total_other_branches}")
        print(f"總新聞數量: {total_news}")
        
        if all_branches_to_delete:
            print(f"\n需要刪除的舊分支: {len(all_branches_to_delete)} 個")
        
        return all_topic_events
    
    def generate_topic_title(self, news_items):
        """為整個主題生成標題"""
        if not self.genai_client or not news_items:
            return f"主題事件 ({len(news_items)} 則新聞)"
        
        # 取前3則新聞的標題和內容片段
        sample_news = []
        for i, news in enumerate(news_items[:3], 1):
            title = news['news_title'][:50]
            content = news['content'][:80]
            sample_news.append(f"新聞{i}: {title} - {content}...")
        
        prompt = f"""
基於以下 {len(news_items)} 則新聞，生成一個簡潔的主題標題。

範例新聞：
{chr(1000).join(sample_news)}

請生成一個8字以內的主題標題，只回傳標題文字，不要其他內容。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            title = response.text.strip().replace('"', '').replace("'", '')
            return title if len(title) <= 20 else title[:17] + "..."
            
        except Exception as e:
            print(f"  ✗ AI 生成主題標題時發生錯誤: {e}")
            return f"主題事件 ({len(news_items)} 則新聞)"
    
    def generate_topic_summary(self, news_items):
        """為主題生成概要"""
        if not self.genai_client or not news_items:
            return f"包含 {len(news_items)} 則相關新聞的主題事件"
        
        # 取前3則新聞的內容
        sample_news = []
        for i, news in enumerate(news_items[:3], 1):
            content = news['content'][:100]
            sample_news.append(f"新聞{i}: {content}...")
        
        prompt = f"""
基於以下新聞內容，生成一個80字以內的事件概要。

新聞內容：
{chr(1000).join(sample_news)}

請生成簡潔的概要說明，只回傳概要文字，不要其他內容。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            summary = response.text.strip()
            return summary if len(summary) <= 100 else summary[:97] + "..."
            
        except Exception as e:
            print(f"  ✗ AI 生成概要時發生錯誤: {e}")
            return f"包含 {len(news_items)} 則相關新聞的主題事件"
    
    def regroup_single_topic(self, topic_id, save_to_db=True):
        """重新分組單個主題並更新到資料庫
        
        Args:
            topic_id: 要重新分組的主題 ID
            save_to_db: 是否寫入資料庫（True=寫入, False=僅預覽）
        
        Returns:
            重新分組後的主題資料
        """
        print("=" * 80)
        print(f"🔄 重新分組單一主題: {topic_id}")
        print("=" * 80)
        
        # 1. 從 topic_news_map 獲取該主題的所有新聞
        try:
            response = self.supabase.table('topic_news_map').select(
                'story_id'
            ).eq('topic_id', topic_id).execute()
            
            if not response.data:
                print(f"✗ 未找到主題 {topic_id} 的新聞映射")
                return None
            
            story_ids = [item['story_id'] for item in response.data]
            print(f"✓ 找到 {len(story_ids)} 則新聞")
            
        except Exception as e:
            print(f"✗ 獲取主題新聞時發生錯誤: {e}")
            return None
        
        # 2. 獲取新聞內容
        news_items = self.fetch_news_from_supabase(story_ids)
        if not news_items:
            print("✗ 未獲取到新聞內容")
            return None
        
        # 3. 生成主題標題
        topic_title = self.generate_topic_title(news_items)
        print(f"✓ 主題標題: {topic_title}")
        
        # 4. 使用 AI 重新分組（考慮最小規模）
        print(f"\n正在重新分組 {len(news_items)} 則新聞...")
        sub_events = self.group_news_by_events_ai_with_min_size(
            news_items,
            min_size=self.MIN_BRANCH_SIZE
        )
        
        # 為每個子事件添加 topic_id
        for sub_event in sub_events:
            sub_event['topic_id'] = topic_id
        
        topic_event = {
            'topic_id': topic_id,
            'topic_title': topic_title,
            'sub_events': sub_events
        }
        
        # 5. 輸出預覽
        print("\n" + "=" * 80)
        print("📊 重新分組結果預覽")
        print("=" * 80)
        print(f"\n【主題】{topic_title}")
        print(f"  主題 ID: {topic_id}")
        print(f"  總新聞數: {len(news_items)}")
        print(f"  分支數量: {len(sub_events)}")
        
        for i, sub_event in enumerate(sub_events, 1):
            is_other = sub_event.get('is_other', False)
            marker = "📦 [暫存區]" if is_other else "📌"
            
            print(f"\n  {marker} 分支 {i}: {sub_event['event_title']}")
            print(f"     分支 ID: {sub_event['event_id']}")
            print(f"     新聞數量: {sub_event['news_count']} 則")
            print(f"     摘要: {sub_event['event_summary'][:80]}...")
            
            # 列出前3則新聞標題
            news_list = sub_event.get('news_items', [])
            if news_list:
                print(f"     包含新聞:")
                for j, news in enumerate(news_list[:3], 1):
                    title = news.get('news_title', '')[:50]
                    print(f"       {j}. {title}{'...' if len(news.get('news_title', '')) > 50 else ''}")
                if len(news_list) > 3:
                    print(f"       ... 還有 {len(news_list) - 3} 則新聞")
        
        # 6. 寫入資料庫
        if save_to_db:
            print("\n" + "=" * 80)
            print("💾 開始更新資料庫...")
            print("=" * 80)
            
            try:
                # Step 1: 刪除該主題的舊分支
                print("\n1. 刪除舊分支...")
                
                # 先找出該主題的所有舊分支 ID
                old_branches_response = self.supabase.table('topic_branch').select(
                    'topic_branch_id'
                ).eq('topic_id', topic_id).execute()
                
                if old_branches_response.data:
                    old_branch_ids = [b['topic_branch_id'] for b in old_branches_response.data]
                    print(f"   找到 {len(old_branch_ids)} 個舊分支")
                    
                    # 刪除 topic_branch_news_map 中的對應關係
                    for branch_id in old_branch_ids:
                        self.supabase.table('topic_branch_news_map').delete().eq(
                            'topic_branch_id', branch_id
                        ).execute()
                    print(f"   ✓ 已刪除 topic_branch_news_map 中的對應關係")
                    
                    # 刪除 topic_branch 中的舊分支
                    self.supabase.table('topic_branch').delete().eq(
                        'topic_id', topic_id
                    ).execute()
                    print(f"   ✓ 已刪除 {len(old_branch_ids)} 個舊分支")
                else:
                    print("   → 該主題無舊分支")
                
                # Step 2: 寫入新分支
                print("\n2. 寫入新分支...")
                
                topic_branch_data = []
                topic_branch_news_map_data = []
                
                for sub_event in sub_events:
                    branch_id = sub_event['event_id']
                    
                    # 準備 topic_branch 資料
                    topic_branch_data.append({
                        'topic_id': topic_id,
                        'topic_branch_id': branch_id,
                        'topic_branch_title': sub_event['event_title'],
                        'topic_branch_content': sub_event['event_summary']
                    })
                    
                    # 準備 topic_branch_news_map 資料
                    for news_item in sub_event.get('news_items', []):
                        topic_branch_news_map_data.append({
                            'topic_branch_id': branch_id,
                            'story_id': news_item['story_id']
                        })
                
                # 批次寫入 topic_branch
                if topic_branch_data:
                    response = self.supabase.table('topic_branch').insert(topic_branch_data).execute()
                    if response.data:
                        print(f"   ✓ 成功寫入 {len(topic_branch_data)} 個新分支")
                    else:
                        print(f"   ✗ 寫入 topic_branch 失敗")
                
                # 批次寫入 topic_branch_news_map
                if topic_branch_news_map_data:
                    batch_size = 100
                    success_count = 0
                    
                    for i in range(0, len(topic_branch_news_map_data), batch_size):
                        batch = topic_branch_news_map_data[i:i + batch_size]
                        response = self.supabase.table('topic_branch_news_map').insert(batch).execute()
                        if response.data:
                            success_count += len(batch)
                    
                    print(f"   ✓ 成功寫入 {success_count}/{len(topic_branch_news_map_data)} 筆新聞對應")
                
                print("\n✅ 資料庫更新完成！")
                
            except Exception as e:
                print(f"\n✗ 資料庫更新時發生錯誤: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("\n" + "=" * 80)
            print("📋 預覽模式（未寫入資料庫）")
            print("=" * 80)
        
        return topic_event
    
    def generate_topic_title_and_summary(self, news_items):
        """使用 AI 為主題生成標題和概要"""
        if not self.genai_client or not news_items:
            return f"主題事件 ({len(news_items)} 則新聞)", f"包含 {len(news_items)} 則相關新聞的主題事件"
        
        # 準備新聞摘要
        news_summaries = []
        for i, news in enumerate(news_items[:5], 1):  # 最多取前5則新聞分析
            title = news['news_title'][:60]
            content = news['content'][:100]
            news_summaries.append(f"新聞{i}: {title} - {content}...")
        
        prompt = f"""
基於以下 {len(news_items)} 則新聞，生成一個簡潔的事件標題和概要。

新聞內容：
{chr(1000).join(news_summaries)}

請以 JSON 格式回傳：
{{
  "title": "簡潔的事件標題（8字以內）",
  "summary": "事件概要說明（80字以內）"
}}

只回傳 JSON，不要其他文字。
"""
        
        try:
            response = self.genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            result_text = response.text.strip()
            
            # 清理 JSON 格式
            if result_text.startswith('```json'):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith('```'):
                result_text = result_text[3:-3].strip()
            
            result = json.loads(result_text)
            return result.get('title', '主題事件'), result.get('summary', f'包含 {len(news_items)} 則相關新聞')
            
        except Exception as e:
            print(f"✗ AI 生成標題和概要時發生錯誤: {e}")
            return f"主題事件 ({len(news_items)} 則新聞)", f"包含 {len(news_items)} 則相關新聞的主題事件"
    
    def process(self, json_file_path, output_path):
        """完整處理流程（原版 - 從JSON檔案開始）"""
        print("=" * 60)
        print("新聞事件分組器 - 開始處理")
        print("=" * 60)
        
        # 1. 讀取 story_id
        story_ids = self.read_story_ids_from_json(json_file_path)
        if not story_ids:
            print("未找到有效的 story_id，程式結束")
            return
        
        # 2. 從 Supabase 獲取新聞
        news_items = self.fetch_news_from_supabase(story_ids)
        if not news_items:
            print("未獲取到任何新聞內容，程式結束")
            return
        
        # 3. 使用 AI 分組
        event_groups = self.group_news_by_events_ai(news_items)
        
        # 4. 儲存結果到 JSON 檔案
        self.save_to_json(event_groups, output_path)
        
        # 5. 儲存結果到資料庫
        self.save_to_database(event_groups)
        
        # 5. 輸出統計資訊
        print("\n" + "=" * 60)
        print("處理完成 - 統計資訊")
        print("=" * 60)
        print(f"原始 story_id 數量: {len(story_ids)}")
        print(f"成功獲取新聞數量: {len(news_items)}")
        print(f"分組後事件分支數量: {len(event_groups)}")
        
        for i, group in enumerate(event_groups, 1):
            print(f"  分支 {i}: {group['event_title']} ({group['news_count']} 則新聞)")


def main():
    """主程式入口 - 增量更新模式"""
    print("🚀 新聞事件分組器 - 啟動中...")
    print("=" * 80)
    print("� 模式：增量更新模式（最小分支規模: 5 則新聞）")
    print("=" * 80)
    print("\n功能特點:")
    print("  ✓ 每個分支至少需要 5 則新聞")
    print("  ✓ 不足 5 則的放入「其他待分類新聞」暫存區")
    print("  ✓ 檢查新新聞是否可加入現有分支")
    print("  ✓ 暫存區+新新聞若達 5 則，自動重新分組")
    print("  ✓ 先輸出預覽到終端，不更動資料庫")
    print()
    
    # 創建處理器
    try:
        grouper = NewsEventGrouper()
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        print("請檢查環境設定和網路連線")
        return
    
    # 設定輸出檔案名稱（包含時間戳記）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"topic_grouped_news_incremental_{timestamp}.json"
    
    # ⚠️ 重要設定
    save_to_db = False  # 先不寫入資料庫，只輸出預覽
    incremental_mode = True  # 啟用增量更新模式
    
    print(f"📄 結果將儲存到: {output_path}")
    print("� 模式: 預覽模式（不會寫入資料庫）")
    print()
    
    try:
        # 執行主要處理流程
        result = grouper.process_from_topic_map(
            output_path, 
            save_to_db=save_to_db,
            incremental_mode=incremental_mode
        )
        
        if result:
            print("\n" + "=" * 80)
            print("🎉 處理完成！")
            print("=" * 80)
            print(f"✅ JSON 檔案: {output_path}")
            print("✅ 詳細結果已輸出到終端")
            print()
            print("📝 下一步:")
            print("  1. 檢查上方終端輸出的分組結果")
            print("  2. 如果結果正確，修改 main() 中的 save_to_db = True")
            print("  3. 重新執行程式即可寫入資料庫")
        else:
            print("\n⚠️ 處理過程中遇到問題，請檢查輸出訊息")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷程式執行")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        print("請檢查網路連線和資料庫設定")
    
    print("\n程式結束")


if __name__ == "__main__":
    main()