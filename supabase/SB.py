from supabase import create_client, Client

url = "https:"
key = "api_key"
supabase: Client = create_client(url, key)

data = {
    "sourceorg_id": "Jay Chou",
    "sourceorg_media": "jay@example.com",
    "title": "jay@example.com",
    "content": "jay@example.com",
    "url": "jay@example.com",
    "date": "2025-04-20T18:30:00"
}

res = supabase.table("which_table").insert(data).execute()
print(res.data)
