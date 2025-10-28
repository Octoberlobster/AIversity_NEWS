from env import supabase, gemini_client
from google.genai import types
from pydantic import BaseModel
import json

def fetch_news_by_date(date: str):
    try:
        response = supabase.table("single_news")\
            .select("story_id, news_title, ultra_short, generated_date")\
            .like("generated_date", f"%{date}%")\
            .execute()
    except Exception as e:
        print(f"Error fetching news by date: {e}")
        return None
    return response.data

def fetch_country(story_id: str):
    try:
        response = supabase.table("stories").select("country").eq("story_id", story_id).execute()
    except Exception as e:
        print(f"Error fetching country: {e}")
        return None
    return response.data[0]["country"]

if __name__ == "__main__":
    date = "2025-10-28"
    news = fetch_news_by_date(date)
    
    country_news = {}
    for news in news:
        country = fetch_country(news["story_id"])
        print(country)
        if country not in country_news:
            country_news[country] = []
        country_news[country].append(news)
    
    print(country_news)