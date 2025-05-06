import json
import os
with open("RolesAnalyze.json", "r", encoding="utf-8") as file:
    data = json.load(file)
for item in data.items():
    role_name = item[1]["Role_Name"]
    analyze_list = item[1]["Analyze"]
    print(f"角色名稱: {role_name}")
    print("分析結果:")
    print(str(analyze_list))

