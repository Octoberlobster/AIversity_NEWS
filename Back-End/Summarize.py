import google.generativeai as genai
import json
from time import sleep
import os
import Combined

api_key = ""
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def summarize(clean_data):
    
    titles = [item['title'] for item in clean_data]
    urls = [item['url'] for item in clean_data]
    contents = [item['content'] for item in clean_data]
    dates = [item['date'] for item in clean_data]

    print("Titles:", titles)
    print("URLs:", urls)
    print("Contents:", contents)
    print("Dates:", dates)
    
    folder = "Summary"
    summary_list = []

    for i in range(len(contents)):
        index=str(i+1)
        summary = model.generate_content("請根據下列新聞文本生成一份摘要，"
                                        "並萃取出主要的關鍵字與事件發生日期。"
                                        "請注意要提取出事件的核心描述、關鍵人物、地點或機構。"
                                        "請以 JSON 格式回傳，格式如下："
                                        "{"
                                        "\"Summary\": \"摘要內容\","
                                        "\"Key\": [\"關鍵字1\", \"關鍵字2\", ...],"
                                        "\"Date\": \"YYYY-MM-DD\""
                                        "\"URL\": \"新聞網址\""
                                        f"\"Index\": {index}"
                                        "}"
                                        "新聞文本："
                                        "Title：" + titles[i] + "。"
                                        "URL：" + urls[i] + "。"
                                        "Content：" + contents[i] + "。"
                                        "Date：" + dates[i] + "。"
                                        )      
        print("Summary:", summary.text)
        file_path = os.path.join(folder, f"Summary{i+1}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(summary.text)
        print(f"結果已儲存至 Summary{i+1}.json")
        summary_list.append(summary.text)
        
    return Combined.combined(summary_list)
