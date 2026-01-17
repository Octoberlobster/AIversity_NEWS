from google import genai
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent.parent / '.env')
# 設定環境變數
api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key)
translate_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
api_key_supabase = os.getenv("SUPABASE_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)