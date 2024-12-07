import google.generativeai as genai
import os

api_key = os.getenv("API_KEY_Gemini")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('南韓總統尹錫悅3日晚間突然發布戒嚴，表示國會已成為破壞自由民主體制的怪物，為了守護國民免於北韓共產勢力的威脅，也為了避免效忠北韓的反國家勢力勾結，因而發動戒嚴。不過，南韓憲法規定，總統宣布戒嚴必須經由國會審議，且國會多數表決通過、要求解除戒嚴時，總統就必須宣布解嚴。隨後，國會190名議員全票通過解除戒嚴，尹錫悅4日清晨宣布取消緊急戒嚴令，並撤回執行戒嚴事務的兵力。根據以上這段新聞內容對他做因果分析')

markdown_content = f"# 因果分析結果\n\n{response.text}"

# 指定檔案名稱
output_file = "analysis_result.md"

# 將內容寫入檔案
with open(output_file, "w", encoding="utf-8") as file:
    file.write(markdown_content)

print(f"結果已儲存至 {output_file}")