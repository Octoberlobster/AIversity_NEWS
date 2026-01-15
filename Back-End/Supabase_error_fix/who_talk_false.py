from env import supabase

def query_who_talk_length():
    response = supabase.rpc("get_who_talk_length").execute()

    if response.data:
        print(f"[OK] 共取得 {len(response.data)} 筆結果")
        for row in response.data:
            print(row)
    else:
        print("[NO DATA] 沒有資料或 RPC 無回傳結果")

def clear_who_talk():
    query = """
    update single_news
    set who_talk = null
    where json_typeof(who_talk) = 'object'
      and json_typeof(who_talk->'who_talk') = 'array'
      and json_array_length(who_talk->'who_talk') <> 3;
    """

    response = supabase.rpc("execute_sql", {"query": query}).execute()
    print("[OK] 已將符合條件的 who_talk 設為 NULL")

def clean_invalid_who_talk():
    response = supabase.rpc("clean_invalid_who_talk").execute()
    print("[OK] 已清空不符合白名單的 who_talk 欄位")

if __name__ == "__main__":
    query_who_talk_length()
    clear_who_talk()
    clean_invalid_who_talk()
