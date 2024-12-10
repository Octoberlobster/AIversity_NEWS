import google.generativeai as genai
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# 指定要讀取的檔案名稱
input_file = "my_news.md"


with open(input_file, "r", encoding="utf-8") as file:
    markdown_content = file.read()

response = model.generate_content("今天你是一位大學教授擅長的領域是政治學，請你對以下的文章進行分析，並發表自己的對於這篇文章的想法"+markdown_content)

with open("output1.md", "w", encoding="utf-8") as file:
    file.write(response.text)

response=model.generate_content("你現在是一位資深的新聞名嘴，請你對以下的文章進行分析，並發表自己的對於這篇文章的想法"+markdown_content)

with open("output2.md", "w", encoding="utf-8") as file:
    file.write(response.text)
