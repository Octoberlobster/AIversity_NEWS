from env import supabase

def clean_relative_news():
    query = """
    DELETE FROM relative_news rn 
    USING (
        SELECT src_story_id,
               dst_story_id,
               MIN(CAST(id AS text)) AS keep_id
        FROM relative_news
        WHERE src_story_id IN (
            SELECT src_story_id
            FROM relative_news
            GROUP BY src_story_id
            HAVING COUNT(*) > 3
        )
        GROUP BY src_story_id, dst_story_id
        HAVING COUNT(*) > 1
    ) dup
    WHERE rn.src_story_id = dup.src_story_id
      AND rn.dst_story_id = dup.dst_story_id
      AND rn.id::text <> dup.keep_id;

    DELETE FROM relative_news rn
    WHERE id IN (
        SELECT id
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY src_story_id ORDER BY id) AS rn
            FROM relative_news
        ) sub
        WHERE sub.rn > 3
    );

    DELETE FROM relative_news
    WHERE src_story_id IN (
        SELECT DISTINCT src_story_id
        FROM relative_news
        WHERE reason !~ '[\u4e00-\u9fff]'
    );
    """

    response = supabase.rpc("execute_sql", {"query": query}).execute()
    print("✅ 已清除 relative_news 中的重複與多餘資料")

if __name__ == "__main__":
    clean_relative_news()
