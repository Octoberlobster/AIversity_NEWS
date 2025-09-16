from google import genai
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
# 設定環境變數
api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=api_key)
api_key_supabase = os.getenv("SUPABASE_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase: Client = create_client(supabase_url, api_key_supabase)