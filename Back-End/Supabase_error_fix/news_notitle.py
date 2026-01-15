from env import supabase

def delete_empty_titles():
    # 找出所有問題資料
    result = (
        supabase.table("single_news")
        .select("story_id, news_title")
        .in_("news_title", ["EMPTY", "", None])
        .execute()
    )

    rows = result.data

    if not rows:
        print("沒有符合條件的資料。")
        return

    story_ids = [row["story_id"] for row in rows]

    print(f"準備刪除 {len(story_ids)} 筆資料...")

    delete_result = (
        supabase.table("single_news")
        .delete()
        .in_("story_id", story_ids)
        .execute()
    )

    print("刪除完成！")
    print(delete_result)


if __name__ == "__main__":
    delete_empty_titles()