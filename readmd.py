import google.generativeai as genai
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# 指定要讀取的檔案名稱
input_file = "analysis_result.md"

# 讀取檔案內容
try:
    with open(input_file, "r", encoding="utf-8") as file:
        markdown_content = file.read()
    print("檔案內容如下：")
    print(markdown_content)
except FileNotFoundError:
    print(f"找不到檔案：{input_file}")

response = model.generate_content(markdown_content+"根據以上的因果分析，生成一篇新聞報導")
print(response.text)
