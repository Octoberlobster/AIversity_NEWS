"""Supabase 連線測試：

功能：
- 嘗試連線 Supabase
- 嘗試從應用層的已知表（Config.SUPABASE_TABLES 或常見表）讀取樣本資料並列印

注意：透過 PostgREST（supabase REST API）通常無法查詢系統 schema（例如 information_schema 或 pg_catalog），
因此如果您想列出所有系統表，請使用具有 service_role 權限的金鑰，或在 Supabase 控制台的 SQL editor 執行查詢。
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("請先在 word_analysis_system/.env 設定 SUPABASE_URL 與 SUPABASE_KEY")
    raise SystemExit(1)

try:
    from supabase import create_client
except Exception:
    print("請先安裝 supabase 客戶端套件：pip install supabase-py postgrest-py")
    raise SystemExit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"已建立 Supabase 連線：{SUPABASE_URL}")

    # 如果環境中提供了 Postgres 連線字串，優先直接使用 psycopg 連線（需要在 .env 中設定 SUPABASE_DB_URL）
    DB_URL = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    if DB_URL:
        try:
            import psycopg
            print("發現 SUPABASE_DB_URL，嘗試使用 psycopg 直接查詢 Postgres...")
            with psycopg.connect(DB_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT schemaname, tablename FROM pg_catalog.pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname, tablename;")
                    rows = cur.fetchall()
                    print(f"找到 {len(rows)} 個表（篩選掉系統 schema），前 200 筆：")
                    for schema, name in rows[:200]:
                        print(f"- {schema}.{name}")
                    # 顯示每個表的前 3 筆資料（最多 10 個表以免輸出太多）
                    for schema, name in rows[:10]:
                        tbl = f"{schema}.{name}"
                        try:
                            cur.execute(f"SELECT * FROM {schema}.{name} LIMIT 3")
                            sample = cur.fetchall()
                            print(f"\n樣本 {tbl}（最多 3 筆）：")
                            for s in sample:
                                print(f"  • {s}")
                        except Exception as e:
                            print(f"  無法讀取樣本 {tbl}: {e}")
            raise SystemExit(0)
        except ModuleNotFoundError:
            print("psycopg 未安裝，請安裝 psycopg[binary] 或 psycopg3 以啟用直接 SQL 查詢，將退回 Supabase REST 嘗試。")
        except Exception as e:
            print(f"直接使用 Postgres 查詢時發生錯誤：{e}\n將退回使用 Supabase REST 嘗試列出應用層表。")

    # 嘗試從 Config 中取得應用層表名
    try:
        from config import Config
        candidate_tables = list(Config.SUPABASE_TABLES.values())
    except Exception:
        candidate_tables = ['comprehensive_reports', 'keyword_explanations']

    print("將嘗試列出下列應用層表的前 5 筆樣本（若有）：", candidate_tables)
    for tbl in candidate_tables:
        try:
            resp = supabase.table(tbl).select('*').limit(5).execute()
            if getattr(resp, 'error', None):
                print(f"- 無法查詢表 {tbl}: {resp.error}")
                continue
            rows = resp.data or []
            print(f"- 表 {tbl}：共取回 {len(rows)} 筆樣本（顯示最多 5 筆）")
            for r in rows:
                print(f"  • {r}")
        except Exception as ex:
            print(f"- 查詢 {tbl} 時發生例外: {ex}")

    print("\n說明：若您需要列出系統表（information_schema 或 pg_catalog），請在 Supabase 控制台的 SQL editor 使用 service_role key 或提供 SUPABASE_DB_URL 並安裝 psycopg。")

except Exception as e:
    print("建立 Supabase 連線或查詢時發生例外：", e)
    print("建議：確認 SUPABASE_URL、SUPABASE_KEY 是否正確；或改用具有 service_role 權限的 key。")
    raise
