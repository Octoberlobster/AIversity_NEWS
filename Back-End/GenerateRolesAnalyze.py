import google.generativeai as genai
import json
from time import sleep
import glob
import os

api_key = ""
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

def get_roles_analyze(news_data, roles_data):
    
    analyze_list = []
    
    for i in range(len(news_data)):
        
        news = news_data[i]
        roles = roles_data[i]
        
        title = news["Title"]
        print("news:", news)
        print("roles:", roles)

        analyze =model.generate_content("請根據下列新聞內容與角色資訊，請每個角色依據自己的背景、觀點及語境，從第三人稱的角度對該新聞事件進行因果分析。請重點說明以下內容："
                                        "1. 事件發生的主要原因與影響因素。"
                                        "2. 這些因素如何導致當前結果，以及可能產生的後續影響。"
                                        "3. 事件可能引發的社會議題、爭議或其他相關議題。"
                                        "4. 每個角色應以外部評論者或觀察者的身份來分析，不作為事件的直接參與者。"
                                        "請以 JSON 格式回傳結果，格式範例如下："
                                        "{"
                                        "\"Role1\": {"
                                        "Role_Name: \"……\","
                                        "\"Analyze\": \"……\""
                                        "},"
                                        "\"Role2\": {"
                                        "\"Role_Name\": \"……\","
                                        "\"Analyze\": \"……\""
                                        "},"
                                        "\"角色3\": {"
                                        "\"Role_Name\": \"……\","
                                        "\"Analyze\": \"……\""
                                        "},"
                                        "\"角色4\": {"
                                        "\"Role_Name\": \"……\","
                                        "\"Analyze\": \"……\""
                                        "}"
                                        "}"
                                        "以下是新聞內容：" + json.dumps(news) + "以下是角色資訊：" + json.dumps(roles))
        print("Analyze:", analyze.text)
        clean_text = analyze.text
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        clean_text = json.loads(clean_text)
        single_analyze = {title: clean_text}
        analyze_list.append(single_analyze)
        file_path = os.path.join("RolesAnalyze", title+"Analyze.json")
        with open(file_path, "w", encoding="utf-8") as file:
            clean_text = json.dumps(clean_text, ensure_ascii=False, indent=4)
            file.write(clean_text)
        print("Analyze file saved as:", file_path)
        print("==========================================")
    print("Done")
    return analyze_list
    

