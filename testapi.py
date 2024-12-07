from serpapi import GoogleSearch
import json, os
api_key = os.getenv("API_KEY_GoogleNews")

params = {
  "api_key": api_key,
  "engine": "google_news",
  "hl": "zh-tw",
  "gl": "tw",
  "q": "南韓戒嚴"
}

search = GoogleSearch(params)
results = search.get_dict()
print(1)
with open('data.json', 'w') as f:
    json.dump(results, f)