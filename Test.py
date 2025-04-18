import google.generativeai as genai
import json
import os
from time import sleep

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

with open('cleaned/cleaned_2025_03_09_23.json', encoding='utf-8') as f:
    data = json.load(f)

contents = [item['Content'] for item in data]
contents = "\n".join(contents)


print("Content:", contents)

with open('test.txt', 'w', encoding='utf-8') as f:
    response=model.generate_content("請你幫我將下列的新聞文本進行分類事件，將原文附在分類後的事件後面，並且將分類後的事件以以下格式回傳，格式如下：" 
                            "事件1:\n原文1\n原文2\n\n"
                            "事件2:\n原文1\n原文2\n\n"
                            "事件3:\n原文1\n原文2\n\n"
                            +contents)
    test = response.text
    f.write(test)
    print("Response:", response.text)
    print("結果已儲存至 test.txt")

