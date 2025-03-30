import json
import google.generativeai as genai
import os
import glob
import re

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key) #報錯再拔掉

model = genai.GenerativeModel('gemini-1.5-pro-002')

# my_Category=["Politics","Social News","Science","Technology","International News",
#              "Lifestyle & Consumer News","Sports","Entertainment","Business & Finance","Health & Wellness"]
#"政治","社會","科學","科技","國際","生活","運動","娛樂","財經","醫療保健"
with open('Combined.json', encoding='utf-8') as f:
    data=json.load(f)
data = str(data)

Tradition_Category = model.generate_content("你是一位專業的新聞編輯，擅長分析新聞內容，並將新聞歸類到適當的分類中。你的目標是根據新聞摘要與關鍵字將新聞分類到以下 10 個類別之一："
                                                "1. Politics（政治） - 包含政府政策、選舉、外交、政黨動態等。"
                                                "2. Social News（社會新聞） - 犯罪、公共安全、社會事件、勞工議題等。"
                                                "3. Science（科學） - 包含科學研究、太空探索、生物科技等。"
                                                "4. Technology（科技） - 包含 AI、大數據、半導體、電子產品等科技發展。"
                                                "5. International News（國際） - 重大國際事件、地緣政治、國際組織相關新聞。"
                                                "6. Lifestyle & Consumer News（生活） - 旅遊、時尚、飲食、消費趨勢等。"
                                                "7. Sports（運動） - 體育賽事、運動員動態、奧運、世界盃等。"
                                                "8. Entertainment（娛樂） - 電影、音樂、藝人新聞、流行文化等。"
                                                "9. Business & Finance（財經） - 經濟政策、股市、企業動態、投資市場等。"
                                                "10. Health & Wellness（醫療保健） - 公共衛生、醫學研究、醫療技術等。"
                                                "請以 JSON 格式回傳分類結果，格式範例如下："
                                                "{"
                                                "\"Politics\": [1, 2, 3],"
                                                "\"Taiwan News\": [4, 5, 6],"
                                                "\"Science\": [7, 8, 9],"
                                                "\"Technology\": [10, 11, 12],"
                                                "\"International News\": [13, 14, 15],"
                                                "\"Lifestyle & Consumer News\": [16, 17, 18],"
                                                "\"Sports\": [19, 20, 21],"
                                                "\"Entertainment\": [22, 23, 24],"
                                                "\"Business & Finance\": [25, 26, 27],"
                                                "\"Health & Wellness\": [28, 29, 30]"
                                                "}"
                                                "其中的數字代表新聞摘要在原始資料中的index。"
                                                "並且請確保每個新聞都被分類到其中一個類別中。"
                                                "以下是需要請你分類的新聞摘要："
                                                +data)
print("Tradition_Category:", Tradition_Category.text)
with open("Tradition_Category.json", "w", encoding="utf-8") as file:
    file.write(Tradition_Category.text)
print("結果已儲存至 Tradition_Category.json")

