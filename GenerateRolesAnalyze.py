import google.generativeai as genai
import json
from time import sleep
import glob
import os

api_key = os.getenv("API_KEY_Gemini2")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')

News_folder = "GenerateNews_EachEvent"
Roles_folder = "Roles"

News_files = glob.glob(os.path.join(News_folder, "*.json"))
Roles_files = glob.glob(os.path.join(Roles_folder, "*.json"))

for i in range(0, len(News_files)):
    with open (News_files[i], "r", encoding="utf-8") as f:
        News = f.read()
    print("News:", News)
    with open (Roles_files[i], "r", encoding="utf-8") as f:
        Roles = f.read()
    print("Roles:", Roles)
    analyze =model.generate_content("請根據下列新聞內容與角色資訊，請每個角色依據自己的立場與觀點，從第一人稱的角度對該新聞事件進行因果分析。請重點說明以下內容："
                                    "1. 事件發生的主要原因與影響因素。"
                                    "2. 這些因素如何導致當前結果，以及可能產生的後續影響。"
                                    "3. 事件可能引發的社會議題、爭議或其他相關議題。"
                                    "請以 JSON 格式回傳結果，格式範例如下："
                                    "{"
                                    "\"Role1\": {"
                                    "\"Role_Name\": \"……\","
                                    "\"Analyze\": \"……\""
                                    "},"
                                    "\"Role2\": {"
                                    "\"Role_Name\": \"……\","
                                    "\"Analyze\": \"……\""
                                    "},"
                                    "}"
                                    "以下是新聞內容：" + News + "以下是角色資訊：" + Roles)
    print("Analyze:", analyze.text)
    name = News_files[i].split("\\")[1].split(".")[0]
    file_path = os.path.join("RolesAnalyze", name+"Analyze.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(analyze.text)
    print("Analyze file saved as:", file_path)
    print("==========================================")
print("Done")


