#!/usr/bin/env python3
"""檢查環境變數是否正確設定"""

import os
from dotenv import load_dotenv

load_dotenv()

print("環境變數檢查:")
print("=" * 60)

# 檢查 Supabase 設定
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f"\n1. SUPABASE_URL:")
if supabase_url:
    # 只顯示前 20 個字元，避免洩漏完整 URL
    print(f"   ✓ 已設定: {supabase_url[:30]}...")
else:
    print("   ✗ 未設定")

print(f"\n2. SUPABASE_KEY:")
if supabase_key:
    print(f"   ✓ 已設定 (長度: {len(supabase_key)} 字元)")
else:
    print("   ✗ 未設定")

# 檢查 Gemini API
gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

print(f"\n3. GEMINI_API_KEY / GOOGLE_API_KEY:")
if gemini_key:
    print(f"   ✓ 已設定 (長度: {len(gemini_key)} 字元)")
else:
    print("   ✗ 未設定")

print("\n" + "=" * 60)

if not all([supabase_url, supabase_key, gemini_key]):
    print("\n⚠️  請檢查 .env 檔案，確保所有必要的環境變數都已設定")
    print("\n需要的環境變數:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_KEY")
    print("  - GEMINI_API_KEY (或 GOOGLE_API_KEY)")
else:
    print("\n✓ 所有必要的環境變數都已設定")
    
    # 測試 Supabase 連線
    print("\n正在測試 Supabase 連線...")
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        print("✓ Supabase 客戶端建立成功")
        
        # 嘗試讀取 generated_image 表
        try:
            response = client.table("generated_image").select("id").limit(1).execute()
            print(f"✓ 成功連接到 generated_image 表")
            if response.data:
                print(f"  表中至少有 {len(response.data)} 筆資料")
        except Exception as e:
            print(f"✗ 讀取 generated_image 表失敗: {e}")
            
    except Exception as e:
        print(f"✗ Supabase 連線失敗: {e}")
