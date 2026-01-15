from env import supabase, gemini_client
from google.genai import types
from pydantic import BaseModel
import json
from datetime import datetime, timezone, timedelta

class TopTenResponse(BaseModel):
    top_ten_story_ids: list[str]

def get_current_time_slot():
    """
    取得最近完成的6小時時段 (抓剛剛過去的6小時新聞)
    返回: (時段標記, 開始時間, 結束時間)
    
    執行時間 -> 抓取範圍:
    - 00:00~06:00 執行 -> 抓 18:00(前一天)~00:00
    - 06:00~12:00 執行 -> 抓 00:00~06:00
    - 12:00~18:00 執行 -> 抓 06:00~12:00
    - 18:00~24:00 執行 -> 抓 12:00~18:00
    """
    tz_taipei = timezone(timedelta(hours=8))
    now = datetime.now(tz_taipei)
    hour = now.hour
    
    # 判斷應該抓哪個已完成的6小時時段
    if 0 <= hour < 6:
        # 凌晨0-6點執行 -> 抓前一天18:00~今天00:00
        slot = "18-24"
        end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=6)
    elif 6 <= hour < 12:
        # 早上6-12點執行 -> 抓今天00:00~06:00
        slot = "00-06"
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=6)
    elif 12 <= hour < 18:
        # 中午12-18點執行 -> 抓今天06:00~12:00
        slot = "06-12"
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=6)
    else:  # 18 <= hour < 24
        # 晚上18-24點執行 -> 抓今天12:00~18:00
        slot = "12-18"
        start_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=6)
    
    return slot, start_time, end_time

def fetch_news_by_time_range(start_time: datetime, end_time: datetime):
    """
    根據時間範圍抓取新聞 (6小時窗口)
    資料庫的 generated_date 格式: "2025-11-08 06:33"
    """
    try:
        # 直接轉成跟資料庫一樣的字串格式 "YYYY-MM-DD HH:MM"
        start_str = start_time.strftime("%Y-%m-%d %H:%M")
        end_str = end_time.strftime("%Y-%m-%d %H:%M")
        
        print(f"查詢時間範圍: {start_str} ~ {end_str}")
        
        response = supabase.table("single_news")\
            .select("story_id, news_title, short, generated_date")\
            .gte("generated_date", start_str)\
            .lt("generated_date", end_str)\
            .execute()
    except Exception as e:
        print(f"Error fetching news by time range: {e}")
        return None
    return response.data

def fetch_country(story_id: str):
    try:
        response = supabase.table("stories").select("country").eq("story_id", story_id).execute()
    except Exception as e:
        print(f"Error fetching country: {e}")
        return None
    return response.data[0]["country"]

def generate_TopTen_news(country: str, news_list: list[dict], top_n: int = 10):
    
    system_instruction = f"""
        你是一位資深的新聞主編和資料分析師，專門分析 **{country}** 的國家級新聞。
        你的任務是讀取使用者提供的 JSON 格式新聞列表，並為 **{country}** 評選出該時段**最多 {top_n} 則**最重要的新聞。

        **【重要：數量彈性原則】**
        -   你應該返回**最多 {top_n} 則**新聞，但不強制必須達到這個數量。
        -   **寧缺毋濫**：只選擇真正重要、符合標準的新聞。
        -   如果該時段只有少於 {top_n} 則重要新聞，只返回符合標準的數量即可。
        -   **至少返回 1 則新聞**，除非所有新聞都完全不符合任何標準。
        
        你必須嚴格遵守以下的**分層優先級 (Hierarchical Priority)** 來進行排序和篩選：

        **【第一優先： {country} 國內新聞】**
        這是你的**首要**考量。你必須優先從 {country} 國內尋找符合以下條件的新聞：
        1.  **國家級影響**：直接影響 **{country}** 政府、國內政策、經濟（例如：央行、關鍵產業）、或國家安全的事件。
        2.  **重大社會/環境事件**：**發生在 {country} 境內**的重大事件，如天災（地震、颱風）、大規模示威、重大公安事故、或全國性的科學 breakthrough。

        **【第二優先： {country} 相關國際新聞】**
        只有在此類新聞重要性極高時才可考慮：
        3.  **國際關係**：**{country}** 作為主要參與者的外交、軍事或重大貿易事件。
        4.  **重大外部衝擊**：對 **{country}** 經濟、國民或安全有**直接且重大**衝擊的國際事件。

        ---
        **【嚴格過濾：不相關的國際新聞】**
        -   你分析的新聞列表中可能包含 {country} 媒體報導的「**其他國家的地區性/內部新聞**」（例如：日本熊害、歐洲皇室動態）。
        -   **這些新聞應該被排除，不要納入最終列表。**
        ---

        **【【最重要規則：主題多樣性演算法】】**
        你的最終列表**必須**代表「不同」的宏觀新聞主題（最多 {top_n} 個）。
        你必須遵循以下**內部思考步驟**來建構你的答案（不要在輸出中顯示這些步驟）：

        -   **步驟 1 (分析與分群)**：閱讀所有的新聞 `short` 內容。在你的內部分析中，將所有關於**同一個宏觀主題**的新聞歸為一類。
            -   *範例*：「候選人A的演說」、「候選人B的反應」、「選票統計結果」... 這些都屬於**單一的「選舉」主題**。
            -   *範例*：「地震災情」、「救援進度」、「捐款統計」... 這些都屬於**單一的「地震」主題**。

        -   **步驟 2 (主題內篩選)**：對於你分出的**每一個「宏觀主題」**，只挑選出**一篇**最能總結該事件、最重要、或最具代表性的 `story_id`。

        -   **步驟 3 (跨主題排序)**：彙總所有在步驟 2 中被選出的 `story_id`（現在你的候選列表都已是不同主題）。

        -   **步驟 4 (最終輸出)**：根據【第一優先】和【第二優先】的標準，對步驟 3 的候選列表進行最終排序，然後輸出最重要的新聞，**最多 {top_n} 則**。

        **結果**：你的最終輸出列表將因此**強制實現多樣性**，絕不會有多篇報導是關於同一個選舉、同一場災難或同一個政策辯論。
        ---

        **【== 嚴厲警告與最終指示 ==】**
        你的任務**絕對嚴格**，不容許任何錯誤。
        1.  **JSON 格式**：你的回應**必須**是、且**只能**是一個完全符合 Pydantic 模型的 JSON 物件。**嚴禁**在 JSON 物件之外添加任何文字、註解、道歉或 ```json 標記。
        2.  **數量限制**：`top_ten_story_ids` 列表長度必須 **1 <= 長度 <= {top_n}**（至少1則，最多{top_n}則）。
        3.  **規則遵守**：你**必須**嚴格遵守上述所有的「分層優先級」、「嚴格過濾」和「主題多樣性演算法」規則。

        任何偏離這些指示的行為都將被視為任務的完全失敗。
        ---

        你的回應**必須**是一個完全符合 Pydantic 模型的 JSON 物件。
        模型定義如下：
        class TopTenResponse(BaseModel):
            top_ten_story_ids: list[str]
    """
    
    user_prompt = f"""
    這是 {country} 該時段的所有新聞資料。請根據你的角色和系統指示（特別是「分層優先級」、「嚴格過濾」和「主題多樣性」規則），
    分析以下 JSON 列表，並回傳**最多 {top_n} 則**最重要新聞的 `story_id`。

    記住：寧缺毋濫，只選擇真正重要的新聞。但至少要返回 1 則新聞，story_id切勿變更。

    新聞資料：
    {json.dumps(news_list, ensure_ascii=False)}
    """
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=TopTenResponse,
        temperature=0.1
    )
    
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_prompt,
            config=config
        )
        
        # 檢查結果數量是否合理 (1 到 top_n 之間)
        response_data = json.loads(response.text)
        result_count = len(response_data.get("top_ten_story_ids", []))
        
        if result_count > top_n:
            print(f"❌ 警告：回傳的新聞數量 ({result_count}) 超過上限 {top_n}")
            return None
        
        if result_count == 0:
            print(f"❌ 錯誤：未返回任何新聞 (至少需要1則)")
            return None
        
        print(f"✅ 成功選出 {result_count} 則焦點新聞 (上限: {top_n})")
        
        return response.text
    except Exception as e:
        print(f"生成焦點新聞時發生錯誤: {e}")
        return None

def get_existing_top_ten(date: str, country: str):
    """
    取得該日期該國家已存在的焦點新聞
    返回: story_ids 列表，如果不存在則返回空列表
    """
    try:
        response = supabase.table("top_ten_news")\
            .select("top_ten_news_id")\
            .eq("date", date)\
            .eq("country", country)\
            .execute()
        
        if response.data and len(response.data) > 0:
            top_ten_data = response.data[0]["top_ten_news_id"]
            # 處理可能的格式：可能是字串或已經是字典
            if isinstance(top_ten_data, str):
                top_ten_data = json.loads(top_ten_data)
            return top_ten_data.get("top_ten_story_ids", [])
        return []
    except Exception as e:
        print(f"⚠️  讀取已存在的焦點新聞時發生錯誤: {e}")
        return []

def save_top_ten_news(date: str, country: str, new_story_ids: list[str]):
    """
    儲存焦點新聞 - 累計模式
    會與當天已存在的新聞合併（去重），而不是覆蓋
    
    參數:
        date: 日期字串 "YYYY-MM-DD"
        country: 國家名稱
        new_story_ids: 新的 story_ids 列表
    """
    try:
        # 1. 取得已存在的焦點新聞
        existing_ids = get_existing_top_ten(date, country)
        
        # 2. 合併新舊 IDs（使用 set 去重，再轉回 list）
        combined_ids = list(set(existing_ids + new_story_ids))
        
        # 3. 顯示合併資訊
        if existing_ids:
            print(f"   📊 已存在: {len(existing_ids)} 則")
            print(f"   ➕ 新增: {len(new_story_ids)} 則")
            print(f"   🔄 去重後: {len(combined_ids)} 則")
        else:
            print(f"   ✨ 首次建立: {len(combined_ids)} 則")
        
        # 4. 儲存（使用 upsert 會自動更新）
        data = {
            "date": date,
            "country": country,
            "top_ten_news_id": {
                "top_ten_story_ids": combined_ids
            }
        }
        supabase.table("top_ten_news").upsert(data).execute()
        print(f"   ✅ 已更新 {country} 在 {date} 的焦點新聞")
        
    except Exception as e:
        print(f"   ❌ 儲存焦點新聞時發生錯誤: {e}")

def final_selection_for_yesterday(yesterday_date_str: str):
    """
    跨日重新篩選：從昨天累積的所有焦點新聞中，精選出最終的 10 篇
    
    參數:
        yesterday_date_str: 昨天的日期字串 "YYYY-MM-DD"
    """
    allow_country = ["Taiwan", "United States of America", "Japan", "Indonesia"]
    
    print(f"\n{'🌟' * 35}")
    print(f"開始為 {yesterday_date_str} 進行最終篩選（從累積新聞中選出 Top 10）")
    print(f"{'🌟' * 35}\n")
    
    for country in allow_country:
        print(f"\n{'─' * 70}")
        print(f"🌍 處理 {country}")
        
        # 1. 取得昨天累積的所有焦點新聞 IDs
        existing_ids = get_existing_top_ten(yesterday_date_str, country)
        
        if not existing_ids:
            print(f"⚠️  {country} 在 {yesterday_date_str} 沒有累積的焦點新聞，跳過")
            continue
        
        print(f"📊 昨天累積: {len(existing_ids)} 則焦點新聞")
        
        # 2. 如果已經 <= 10 篇，不需要重新篩選
        if len(existing_ids) <= 10:
            print(f"✅ 已經 <= 10 篇，無需重新篩選")
            continue
        
        # 3. 從資料庫抓取這些新聞的完整資訊
        try:
            response = supabase.table("single_news")\
                .select("story_id, news_title, short, generated_date")\
                .in_("story_id", existing_ids)\
                .execute()
            news_list = response.data
        except Exception as e:
            print(f"❌ 抓取新聞資料失敗: {e}")
            continue
        
        if not news_list:
            print(f"⚠️  無法取得新聞詳細資料，跳過")
            continue
        
        print(f"📰 成功載入 {len(news_list)} 則新聞資料")
        
        # 4. 使用 AI 從這些新聞中重新篩選出最重要的 10 篇
        print(f"🤖 正在從 {len(news_list)} 則中精選最終 10 篇...")
        
        final_top_ten = generate_TopTen_news(country, news_list, top_n=10)
        
        if final_top_ten:
            final_result = json.loads(final_top_ten)
            selected_count = len(final_result["top_ten_story_ids"])
            
            print(f"✨ 最終精選: {selected_count} 則")
            for idx, story_id in enumerate(final_result["top_ten_story_ids"], 1):
                print(f"   {idx}. {story_id}")
            
            # 5. 覆蓋儲存（直接替換成最終版本）
            try:
                data = {
                    "date": yesterday_date_str,
                    "country": country,
                    "top_ten_news_id": {
                        "top_ten_story_ids": final_result["top_ten_story_ids"]
                    }
                }
                supabase.table("top_ten_news").upsert(data).execute()
                print(f"✅ 已更新為最終版本 ({len(existing_ids)} → {selected_count} 篇)")
            except Exception as e:
                print(f"❌ 儲存最終版本失敗: {e}")
        else:
            print(f"❌ 最終篩選失敗")
    
    print(f"\n{'🌟' * 35}")
    print(f"✅ {yesterday_date_str} 最終篩選完成！")
    print(f"{'🌟' * 35}\n")

def process_time_slot(date: str, time_slot: str, start_time: datetime, end_time: datetime):
    """
    處理單一時段的焦點新聞生成
    只分析該時段的新聞，然後累加到當天的總列表
    
    參數:
        date: 日期字串 "YYYY-MM-DD"
        time_slot: 時段標記 "00-06", "06-12", "12-18", "18-24"
        start_time: 時段開始時間
        end_time: 時段結束時間
    """
    allow_country = ["Taiwan", "United States of America", "Japan", "Indonesia"]
    
    print(f"\n{'─' * 70}")
    print(f"🕐 時段: {time_slot}")
    print(f"⏰ 時間範圍: {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}")
    
    # 抓取該時段的新聞
    news_list = fetch_news_by_time_range(start_time, end_time)
    
    if not news_list:
        print(f"⚠️  {time_slot} 時段沒有新聞資料，跳過")
        return
    
    print(f"📰 共抓取到 {len(news_list)} 則新聞")
    
    # 按國家分類新聞
    country_news = {}
    for news in news_list:
        country = fetch_country(news["story_id"])
        if country not in allow_country:
            continue
        if country not in country_news:
            country_news[country] = []
        country_news[country].append(news)
    
    # 為每個國家生成焦點新聞
    for country, country_news_items in country_news.items():
        news_count = len(country_news_items)
        print(f"\n  🌍 處理 {country}: {news_count} 則新聞")
        
        # 動態調整上限：最多10則，但不超過實際新聞數量
        max_news = min(10, news_count)
        print(f"     📊 本時段上限: {max_news} 則")
        
        top_ten = generate_TopTen_news(country, country_news_items, top_n=max_news)
        
        if top_ten:
            top_ten_result = json.loads(top_ten)
            selected_count = len(top_ten_result["top_ten_story_ids"])
            
            print(f"  ✨ {country} 本時段焦點新聞 ({selected_count} 則):")
            for idx, story_id in enumerate(top_ten_result["top_ten_story_ids"], 1):
                print(f"     {idx}. {story_id}")
            
            # 儲存結果 (累計模式 - 會與當天已有的合併)
            save_top_ten_news(date, country, top_ten_result["top_ten_story_ids"])
        else:
            print(f"  ❌ {country} 焦點新聞生成失敗")

def run_specific_date(target_date_str: str):
    """
    執行指定日期的所有時段 (00-06, 06-12, 12-18, 18-24)
    每個時段只分析該時段的新聞，然後累加到當天
    
    參數:
        target_date_str: 日期字串，格式 "YYYY-MM-DD"，例如 "2025-11-07"
    """
    # 定義所有時段
    time_slots = [
        ("00-06", 0, 6, 0),      # 00:00 ~ 06:00
        ("06-12", 6, 12, 0),     # 06:00 ~ 12:00
        ("12-18", 12, 18, 0),    # 12:00 ~ 18:00
        ("18-24", 18, 23, 59)    # 18:00 ~ 23:59
    ]
    
    print(f"\n{'=' * 70}")
    print(f"📅 開始處理日期: {target_date_str}")
    print(f"💡 模式: 每時段只分析該時段新聞，累加到當天總列表")
    print(f"{'=' * 70}\n")
    
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    
    # 逐個時段處理
    for slot_name, start_hour, end_hour, end_minute in time_slots:
        # 計算時間範圍
        start_time = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = target_date.replace(hour=end_hour, minute=end_minute, second=59, microsecond=999999)
        
        # 處理該時段
        process_time_slot(target_date_str, slot_name, start_time, end_time)
    
    print(f"\n{'=' * 70}")
    print(f"✅ {target_date_str} 所有時段處理完成!")
    print(f"{'=' * 70}\n")

if __name__ == "__main__":
    
    # ========== 選擇執行模式 ==========
    # 模式 1: 執行當前時段 (正常定時執行用)
    # 模式 2: 補跑歷史日期的所有時段
    
    MODE = "history"  # "current" 或 "history"
    
    if MODE == "history":
        dates_to_run = [
            "2025-11-20"
        ]
        
        print(f"\n{'🎯' * 35}")
        print(f"準備補跑 {len(dates_to_run)} 天的焦點新聞 (累計模式)")
        print(f"{'🎯' * 35}\n")
        
        for date_str in dates_to_run:
            run_specific_date(date_str)

            # 執行該日期的最終篩選  ←  然後馬上進行最終篩選
            print(f"\n{'🌟' * 35}")
            print(f"為 {date_str} 執行最終篩選")
            print(f"{'🌟' * 35}")
            # final_selection_for_yesterday(date_str)  # ← 進行最終篩選
        
        print(f"\n{'🎉' * 35}")
        print(f"✅ 全部完成! 共處理 {len(dates_to_run)} 天")
        print(f"{'🎉' * 35}\n")
    
    else:  # MODE == "current"
    # 正常模式：執行當前時段（只分析該時段新聞）
        time_slot, start_time, end_time = get_current_time_slot()
        date = start_time.strftime("%Y-%m-%d")
        
        print(f"=" * 60)
        print(f"🕐 執行時段: {time_slot}")
        print(f"📅 日期: {date}")
        print(f"⏰ 時間範圍: {start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"💡 模式: 只分析該時段新聞，累加到當天總列表")
        print(f"=" * 60)
        
        process_time_slot(date, time_slot, start_time, end_time)
        
        print(f"\n{'=' * 60}")
        print(f"✅ 完成! 下次更新時間: {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'=' * 60}")