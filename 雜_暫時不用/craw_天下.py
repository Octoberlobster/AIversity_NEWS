# crawl_天下.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import json
import google.generativeai as genai
import os
import clean
import time
import grpc

# 設定請求 URL
url = "https://www.cw.com.tw/article/5134209"
response = requests.get(url)
print(response.status_code)
print(response.text)