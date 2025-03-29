import os
import json
from bs4 import BeautifulSoup
import google.generativeai as genai
from time import sleep

# === 1. 設定資料夾路徑 ===
input_folder = "json/test"
output_folder = "json/processed"

# 確保輸出資料夾存在
os.makedirs(output_folder, exist_ok=True)

api_key = "AIzaSyDwNOkobaknphQQx8NqSVZ6bDSvW_pizlg"

if not api_key or api_key == "YOUR_GEMINI_API_KEY":
    raise ValueError("請先設定你的 GEMINI_API_KEY，或於程式中直接指定。")

# 設定 Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')

# === 2. 處理資料夾內所有檔案 ===
for filename in os.listdir(input_folder):
    if filename.endswith(".txt"):
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, f"similarty_{filename}")

        # 讀txt檔案
        with open(input_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # 根據分隔線切割成多篇新聞
        articles = [a.strip() for a in raw_text.split('--------------------------------------------------') if a.strip()]
        
        # 組合成資料給 Gemini
        combined_data = ""
        for idx, article in enumerate(articles, start=1):
            combined_data += f"[{idx}]\n{article}\n\n"
        print(combined_data [:500])

        # 組合 Prompt
        res = model.generate_content( """
        請根據以下多則新聞，分析每篇新聞的主題，並找出報導內容相似的新聞台。

        請先將內容主題相近的新聞分為同一群組，再列出每個群組中的新聞台、標題與簡要摘要。格式如下：

        ==================================================
        主題名稱：XXX事件
        --------------------------------------------------
        新聞台：TVBS、新頭殼、中央社
        新聞索引：1, 2, 5

        新聞標題與摘要：
        [1] TVBS - 「警察與民眾衝突升溫，總統回應」
        摘要：警方與示威民眾的衝突升高，總統表示將全面調查...

        [2] 新頭殼 - 「街頭抗議升溫，政府出面回應」
        摘要：針對連日的街頭抗議，政府終於在今日召開記者會...

        [5] 中央社 - 「總統談近期抗議事件」
        摘要：總統於今日表示，警方執法將檢討，保障人民權益...

        ==================================================
        主題名稱：YYY事件
        ...

        請依據以下新聞資料進行分析：
        """ + combined_data)

        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(res.text)
        print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    