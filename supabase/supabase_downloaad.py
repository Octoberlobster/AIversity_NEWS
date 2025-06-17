from supabase import create_client, Client
import json

url = "https://gnvfwjxdyvmlozalbxbr.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdudmZ3anhkeXZtbG96YWxieGJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzMjQ1NTksImV4cCI6MjA1NTkwMDU1OX0.qEZgR4YgY54fh-4Ou4pHt1cdIBZyyKr2C3BPCCpzGdg"
supabase: Client = create_client(url, key)

# 查詢 cleaned_news 中 sourcecle_media = 'UDN' 的資料
response = supabase.table("crawler_news") \
    .select("*") \
    .eq("sourceorg_media", "UDN") \
    .execute()

# 顯示查詢結果
# 寫入 JSON 檔案
with open("udn_data.json", "w", encoding="utf-8") as f:
    json.dump(response.data, f, ensure_ascii=False, indent=4)

print("✅ 資料已寫入 UDN_data.json")