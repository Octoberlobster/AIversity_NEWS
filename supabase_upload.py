import json
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from typing import List, Dict, Any, Tuple

def setup_supabase() -> Client:
    """設置 Supabase 客戶端"""
    # 請替換為您的 Supabase URL 和 API Key
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

def load_json_data(file_path: str) -> List[Dict[Any, Any]]:
    """載入 JSON 檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"錯誤: JSON 解析失敗 - {e}")
        return []

def parse_crawl_date(date_str: str) -> datetime:
    """解析 crawl_date 字串為 datetime 物件"""
    try:
        # 假設格式為 "2025/08/15 00:43"
        return datetime.strptime(date_str, "%Y/%m/%d %H:%M")
    except ValueError:
        try:
            # 嘗試其他可能格式
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"警告: 無法解析日期格式: {date_str}")
            return datetime.now()

def check_story_exists(supabase: Client, story_url: str) -> Tuple[bool, str]:
    """檢查 story_url 是否已存在，回傳 (是否存在, 最新 crawl_date)"""
    try:
        response = (
            supabase.table("stories")
            .select("crawl_date", "story_id")
            .eq("story_url", story_url)
            .order("crawl_date", desc=True)   # 取最新一筆
            .limit(1)
            .execute()
        )
        if response.data:
            return True, response.data[0]["crawl_date"], response.data[0]["story_id"]
        return False, "", ""
    except Exception as e:
        print(f"檢查故事是否存在時發生錯誤: {e}")
        return False, ""

def should_update_story(existing_crawl_date: str, new_crawl_date: str) -> bool:
    """判斷是否應該更新故事（新的 crawl_date 是否比既有的晚 3 天以上）"""
    try:
        existing_date = parse_crawl_date(existing_crawl_date)
        new_date = parse_crawl_date(new_crawl_date)
        
        # 計算日期差異
        date_diff = new_date - existing_date
        
        # 如果新日期比既有日期晚 3 天以上，則更新
        return date_diff.days >= 3
    except Exception as e:
        print(f"比較日期時發生錯誤: {e}")
        return False

def upload_stories(supabase: Client, news_data: List[Dict[Any, Any]]) -> Tuple[bool, List[str]]:
    """上傳故事資料到 stories 表，回傳 (是否成功, 已上傳的story_ids)"""
    stories_to_upload = []
    uploaded_story_ids = []
    skipped_count = 0
    updated_count = 0
    new_count = 0
    
    print("正在檢查故事資料...")
    
    for item in news_data:
        story_url = item.get("story_url")
        new_crawl_date = item.get("crawl_date")
        story_id = item.get("story_id")
        
        # 檢查 story_url 是否已存在
        exists, existing_crawl_date, story_idSU = check_story_exists(supabase, story_url)

        if not exists or (story_idSU==story_id):
            # 新故事，直接加入上傳列表
            story_record = {
                "story_id": story_id,
                "story_title": item.get("story_title"),
                "story_url": story_url,
                "crawl_date": new_crawl_date,
                "category": item.get("category")
            }
            stories_to_upload.append(story_record)
            uploaded_story_ids.append(story_id)
            new_count += 1
            print(f"新故事: {item.get('story_title')[:50]}...")
    
    print(f"\n處理結果:")
    print(f"  新增: {new_count} 筆")
    print(f"  更新: {updated_count} 筆")
    print(f"  跳過: {skipped_count} 筆")
    print(f"  總共需上傳: {len(stories_to_upload)} 筆")
    
    if not stories_to_upload:
        print("沒有需要上傳的故事資料")
        return True, []
    
    try:
        # 使用 upsert 避免重複插入
        response = supabase.table("stories").upsert(stories_to_upload).execute()
        print(f"成功上傳 {len(stories_to_upload)} 筆故事資料到 stories 表")
        return True, uploaded_story_ids
    except Exception as e:
        print(f"上傳 stories 資料時發生錯誤: {e}")
        return False, []

def upload_articles(supabase: Client, news_data: List[Dict[Any, Any]], uploaded_story_ids: List[str]) -> bool:
    """上傳文章資料到 cleaned_news 表，只上傳已成功上傳的故事對應的文章，避免重複"""
    articles_data = []
    
    for item in news_data:
        story_id = item.get("story_id")
        
        # 只處理已成功上傳的故事
        if story_id not in uploaded_story_ids:
            continue
            
        articles = item.get("articles", [])
        
        for article in articles:
            article_url = article.get("article_url")

            # 🔎 檢查是否已有相同 article_url
            try:
                existing = (
                    supabase.table("cleaned_news")
                    .select("article_id")
                    .eq("article_url", article_url)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    print(f"跳過文章（已存在）: {article.get('article_title')[:50]}...")
                    continue
            except Exception as e:
                print(f"檢查文章是否存在時發生錯誤: {e}")
                continue

            article_record = {
                "article_id": article.get("article_id"),
                "article_title": article.get("article_title"),
                "article_url": article_url,
                "media": article.get("media"),
                "content": article.get("content"),
                "story_id": story_id
            }
            articles_data.append(article_record)
    
    if not articles_data:
        print("沒有需要上傳的文章資料")
        return True
    
    try:
        # 分批上傳以避免單次請求過大
        batch_size = 100
        total_articles = len(articles_data)
        
        for i in range(0, total_articles, batch_size):
            batch = articles_data[i:i + batch_size]
            supabase.table("cleaned_news").upsert(batch).execute()
            print(f"已上傳 {min(i + batch_size, total_articles)}/{total_articles} 筆文章資料")
        
        print(f"成功上傳 {total_articles} 筆文章資料到 cleaned_news 表")
        return True
    except Exception as e:
        print(f"上傳 cleaned_news 資料時發生錯誤: {e}")
        return False

def main():
    """主函數"""
    # JSON 檔案路徑
    json_file_path = "json/processed/cleaned_final_news.json"  # 請確認檔案路徑
    
    print("開始處理新聞資料上傳...")
    
    # 1. 設置 Supabase 客戶端
    print("設置 Supabase 連接...")
    supabase = setup_supabase()
    
    # 2. 載入 JSON 資料
    print(f"載入 JSON 檔案: {json_file_path}")
    news_data = load_json_data(json_file_path)
    
    if not news_data:
        print("沒有資料可上傳，程式結束")
        return
    
    print(f"載入了 {len(news_data)} 筆故事資料")
    
    # 3. 上傳 stories 資料
    print("\n開始上傳 stories 資料...")
    stories_success, uploaded_story_ids = upload_stories(supabase, news_data)
    
    if not stories_success:
        print("stories 資料上傳失敗，停止程式")
        return
    
    if not uploaded_story_ids:
        print("沒有新的或需要更新的故事，程式結束")
        return
    
    # 4. 上傳 articles 資料
    print("\n開始上傳 articles 資料...")
    articles_success = upload_articles(supabase, news_data, uploaded_story_ids)
    
    if articles_success:
        print("\n✅ 所有資料上傳完成！")
    else:
        print("\n❌ articles 資料上傳失敗")

if __name__ == "__main__":
    # 執行主程式
    main()