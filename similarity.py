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
        請仔細閱讀以下多篇新聞，並完成以下分析：

        1. 依「日期」整理：
        - 根據新聞發布或事件發生的日期，將新聞先做初步分類。  
        - 若新聞中未明確提到日期，請使用報導發布日期或註明「日期不明」。

        2. 在每個日期範圍內，找出內容相近的新聞：
        - 針對同一天（或連續數天）的新聞，比較其內容是否聚焦在相同主題或事件。  
        - 將內容相似的新聞歸為同一小群組，並標註該群組的主題名稱。  
        - 在同一小群組中，列出各個新聞台、新聞索引、標題與簡要摘要。

        3. 呈現方式範例：
        - 建議以「日期 → 相似新聞群組 → 新聞台/標題/摘要」的結構呈現，例如：
            ```
            ==================================================
            日期：2025-04-01
            --------------------------------------------------
            主題名稱：街頭抗議升溫
            新聞台：TVBS、新頭殼
            新聞索引：1, 3

            新聞標題與摘要：
            [1] TVBS - 「警察與民眾衝突升溫，總統回應」
            摘要：警方與示威民眾的衝突升高，總統表示將全面調查...

            [3] 新頭殼 - 「街頭抗議升溫，政府出面回應」
            摘要：針對連日的街頭抗議，政府終於在今日召開記者會...

            ==================================================
            日期：2025-04-02
            --------------------------------------------------
            主題名稱：...
            新聞台：...
            新聞索引：...
            ...
            ```

        4. 結合時序與內容分析：
        - 在最終結論中，可以簡要指出：  
            - 連續幾天是否有相同主題的新聞台在報導類似內容？  
            - 該主題的新聞台是否隨著時間發生變化（例如：有更多電視台開始關注某事件）？  
        - 如有需要，可在最後加一小段「整體觀察」，說明整個時序脈絡下，新聞台報導焦點是否有轉移或升級。

        請依上述指示整理以下新聞資料：
        """ + combined_data)

        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(res.text)
        print(f"{filename} 已處理完畢，儲存至 {output_file_path}")
print("所有檔案處理完成！")    