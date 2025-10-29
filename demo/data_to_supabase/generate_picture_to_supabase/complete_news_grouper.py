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
    
    def group_news_by_events_ai(self, news_items):
        """使用 Gemini AI 將新聞分組為事件分支"""
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
    
    def process_from_topic_map(self, output_path, save_to_db=True):
        """使用 topic_news_map 的處理流程
        
        Args:
            output_path: JSON 輸出檔案路徑
            save_to_db: 是否儲存到資料庫 (True=儲存, False=僅預覽)
        """
        print("=" * 60)
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
        
        for topic_id, story_ids in topic_groups.items():
            print(f"\n處理主題 {topic_id} ({len(story_ids)} 則新聞)...")
            
            # 獲取該主題的新聞內容
            news_items = self.fetch_news_from_supabase(story_ids)
            
            if not news_items:
                print(f"✗ 主題 {topic_id}: 未獲取到有效新聞內容")
                continue
            
            # 為該主題生成總體標題
            topic_title = self.generate_topic_title(news_items)
            print(f"✓ 主題 {topic_id}: {topic_title}")
            
            # 如果新聞數量較少（<=3則），直接作為一個分支
            if len(news_items) <= 3:
                topic_summary = self.generate_topic_summary(news_items)
                topic_event = {
                    'topic_id': topic_id,
                    'topic_title': topic_title,
                    'sub_events': [
                        {
                            'event_id': str(uuid.uuid4()),
                            'event_title': topic_title,
                            'event_summary': topic_summary,
                            'news_count': len(news_items),
                            'news_items': news_items
                        }
                    ]
                }
                all_topic_events.append(topic_event)
                print(f"  → 單一分支: {topic_title} ({len(news_items)} 則新聞)")
            
            else:
                # 新聞數量較多，使用 AI 進行細分
                print(f"  正在對 {len(news_items)} 則新聞進行 AI 細分...")
                sub_events = self.group_news_by_events_ai(news_items)
                
                # 為每個子事件添加 topic 相關資訊
                for sub_event in sub_events:
                    sub_event['topic_id'] = topic_id
                
                topic_event = {
                    'topic_id': topic_id,
                    'topic_title': topic_title,
                    'sub_events': sub_events
                }
                all_topic_events.append(topic_event)
                
                print(f"  → 細分為 {len(sub_events)} 個分支:")
                for i, sub_event in enumerate(sub_events, 1):
                    print(f"    分支 {i}: {sub_event['event_title']} ({sub_event['news_count']} 則新聞)")
        
        # 4. 儲存結果到 JSON
        self.save_to_json(all_topic_events, output_path)
        
        # 5. 儲存到資料庫或生成預覽
        if save_to_db:
            save_mode = "both"  # 同時生成預覽和儲存到資料庫
            print("\n將同時生成預覽檔案並儲存到資料庫...")
        else:
            save_mode = "preview"  # 僅生成預覽
            print("\n僅生成資料庫預覽檔案...")
        
        self.save_to_database(all_topic_events, save_mode)
        
        # 6. 輸出統計資訊
        print("\n" + "=" * 60)
        print("處理完成 - 統計資訊")
        print("=" * 60)
        print(f"主題數量: {len(topic_groups)}")
        print(f"成功處理的主題: {len(all_topic_events)}")
        
        total_sub_events = sum(len(topic['sub_events']) for topic in all_topic_events)
        total_news = sum(
            sum(sub_event['news_count'] for sub_event in topic['sub_events'])
            for topic in all_topic_events
        )
        print(f"總分支數量: {total_sub_events}")
        print(f"總新聞數量: {total_news}")
        
        for i, topic in enumerate(all_topic_events, 1):
            print(f"\n主題 {i}: {topic['topic_title']} (ID: {topic['topic_id']})")
            for j, sub_event in enumerate(topic['sub_events'], 1):
                print(f"  分支 {j}: {sub_event['event_title']} ({sub_event['news_count']} 則新聞)")
        
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
    """主程式入口 - 直接執行即可"""
    print("🚀 新聞事件分組器 - 啟動中...")
    print("💾 模式：從 topic_news_map 讀取資料，AI分組後儲存到資料庫")
    print("=" * 60)
    
    # 創建處理器
    try:
        grouper = NewsEventGrouper()
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        print("請檢查環境設定和網路連線")
        return
    
    # 設定輸出檔案名稱（包含時間戳記）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"topic_grouped_news_{timestamp}.json"
    
    # 預設模式：從 topic_news_map 處理並儲存到資料庫
    save_to_db = True
    
    print(f"📄 結果將儲存到: {output_path}")
    print("💾 將同時生成預覽檔案並儲存到資料庫")
    print()
    
    try:
        # 執行主要處理流程
        result = grouper.process_from_topic_map(output_path, save_to_db)
        
        if result:
            print("\n🎉 處理完成！")
            print(f"✅ JSON 檔案: {output_path}")
            print("✅ 資料庫預覽檔案: database_preview_*.json")
            print("✅ 資料已儲存到 Supabase 資料庫")
        else:
            print("\n⚠️ 處理過程中遇到問題，請檢查輸出訊息")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 使用者中斷程式執行")
    except Exception as e:
        print(f"\n❌ 執行過程中發生錯誤: {e}")
        print("請檢查網路連線和資料庫設定")
    
    print("\n程式結束")


if __name__ == "__main__":
    main()