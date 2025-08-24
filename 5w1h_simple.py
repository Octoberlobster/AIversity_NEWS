from google import genai
import os
import json

# 設定 API Key
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
client = genai.Client()

# 定義 prompt
prompt = """
你是一個專業的新聞與專題 AI 助手，專門提供某一事件或議題的簡明完整分析。請根據使用者提供的事件或主題，回答以下問題，並以簡潔、條列式的方式呈現：

1. Who（誰）：事件的主要人物、組織或群體。
2. What（什麼）：事件的核心內容或行動。
3. When（何時）：事件發生的時間或期間。
4. Where（哪裡）：事件發生的地點或範圍。
5. Why（為什麼）：事件的原因、背景或動機。
6. How（如何發生）：事件的過程或運作方式。

要求：
- 內容必須正確且可驗證。
- 條列簡明扼要，不超過 5 行文字/每個 5W1H。
- 使用清楚、正式的新聞或報告風格語言。
- 不提供無關資訊或個人評論。

最後將結果輸出成json
output_folder = "json/5W1H"

例子輸入：大罷免
例子輸出：
Who: 某政黨議員、罷免發起團體
What: 發起對特定議員的罷免投票
When: 2025 年 8 月
Where: 某縣市選區
Why: 對議員施政不滿或爭議事件
How: 依選舉法進行公民投票

請幫我分析2025台灣大罷免
"""

# 使用模型生成回答
response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents=prompt,
    tools=['google_search']
)

# 印出回應文字
print(response.text)
