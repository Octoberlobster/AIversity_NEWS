import google.generativeai as genai
import json
from time import sleep
import os
import Combined

api_key = ""
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def summarize(clean_data):
    
    titles = [item['Title'] for item in clean_data]
    urls = [item['URL'] for item in clean_data]
    contents = [item['Content'] for item in clean_data]
    dates = [item['Date'] for item in clean_data]

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
                                        "請注意要提取出事件的核心描述、關鍵人物、地點或機構，不加入任何自行的想法。"
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
        clean_summary_text = summary.text
        clean_summary_text = clean_summary_text.replace("```json", "").replace("```", "").strip()
        clean_summary_text = json.loads(clean_summary_text)
        summary_list.append(clean_summary_text)
        file_path = os.path.join(folder, f"Summary{i+1}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            clean_summary_text = json.dumps(clean_summary_text, ensure_ascii=False, indent=4)
            file.write(clean_summary_text)
        print(f"結果已儲存至 Summary{i+1}.json")
        
        
    return Combined.combined(summary_list)
