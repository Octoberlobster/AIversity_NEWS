import google.generativeai as genai
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-pro')

input_file = "input.md"
with open(input_file,"r",encoding="utf-8") as file:
    markdown_content = file.read()

response = model.generate_content(markdown_content+"根據以上的眾多新聞中，生成一篇新聞報導，以供主播報導")


# 指定檔案名稱
output_file = "my_news.md"

# 將內容寫入檔案
with open(output_file, "w", encoding="utf-8") as file:
    file.write(response.text)

print(f"結果已儲存至 {output_file}")