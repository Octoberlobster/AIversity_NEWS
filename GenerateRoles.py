import google.generativeai as genai
import json
from time import sleep
import glob
import os

api_key = os.getenv("API_KEY_Gemini2")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-pro-002')

folder = "GenerateNews_EachEvent"

json_files = glob.glob(os.path.join(folder, "*.json"))

for filename in json_files:
    with open (filename, "r", encoding="utf-8") as f:
        data = f.read()
    print("Data:", data)

    Roles = model.generate_content("請根據下列新聞內容，分析該新聞事件可能涉及的重要角色，並生成四個角色。每個角色請包含以下資訊："
                                   "1. 角色名稱：描述該角色在事件中扮演的角色（例如：政府機關、相關人士、專家、受影響民眾等）。"
                                   "2. 角色背景：簡述該角色的專業背景、所屬領域或與事件相關的經歷，說明他們為何對該事件具有影響力或見解。"
                                   "3. 角色觀點：描述該角色可能對事件提出的觀點、立場或分析，並說明他們可能關注的議題。"
                                   "4. 語境：描述該角色所處的環境與上下文，包括角色與事件之間的關係、所在的時空背景、媒體關注度等。"
                                   "請注意：生成的角色必須以第三人稱角度來看待該事件，角色應作為外部觀察者或評論者，而非事件本身的直接參與者。"
                                   "請以 JSON 格式回傳結果，格式範例如下："
                                   "{"
                                   "'Role1': {"
                                   "'Role_Name': '……',"
                                   "'Role_Background': '……',"
                                   "'Role_View': '……',"
                                   "'Context': '……'"
                                   "},"
                                   "'Role2': {"
                                   "'Role_Name': '……',"
                                   "'Role_Background': '……',"
                                   "'Role_View': '……',"
                                   "'Context': '……'"
                                   "},"
                                   "'角色3': {"
                                   "'Role_Name': '……',"
                                   "'Role_Background': '……',"
                                   "'Role_View': '……',"
                                   "'Context': '……'"
                                   "},"
                                   "'角色4': {"
                                   "'Role_Name': '……',"
                                   "'Role_Background': '……',"
                                   "'Role_View': '……',"
                                   "'Context': '……'"
                                   "}"
                                   "}"
                                   "以下是新聞內容："
                                    +data
                                    )
    print("Roles:", Roles.text)
    name = filename.split("\\")[1].split(".")[0]
    file_path = os.path.join("Roles", name+"Roles.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(Roles.text)
    print("結果已儲存至 Roles.json")
    sleep(60)
print("所有角色已生成完畢")
