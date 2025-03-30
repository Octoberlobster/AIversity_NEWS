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

    Roles = model.generate_content(data+"請根據以上新聞內容，請你以以下角色的身分，幫我生成他們的對這事件的立場與看法，並以文字描述。"
                                    "1. 美國政府"
                                    "2. 烏克蘭政府"
                                    "3. 俄羅斯政府"
                                    "4. 台灣政府"
                                    "5. 戰地平民"
                                    "6. 歐盟"
                                    "請以 JSON 格式回傳："
                                    "{"
                                    "\"Roles\": ["
                                    "{"
                                    "\"Role\": \"\","
                                    "\"Viewpoint\": \"\""
                                    "},"
                                    "{"
                                    "\"Role\": \"\","
                                    "\"Viewpoint\": \"\""
                                    "},")
    print("Roles:", Roles.text)
    file_path = os.path.join("Roles\\Roles.json")
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(Roles.text)
    print("結果已儲存至 Roles.json")
print("所有角色已生成完畢")
