import google.generativeai as genai
import json
from time import sleep
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')